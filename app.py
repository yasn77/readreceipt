from __future__ import annotations

import csv
import io
import json
import logging
import os
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import update_wrapper, wraps
from io import StringIO
from typing import Any

from authlib.integrations.flask_client import OAuth
from flask import (
    Flask,
    g,
    json,
    make_response,
    redirect,
    request,
    send_file,
    session,
    url_for,
)
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from sqlalchemy_utils import CountryType, IPAddressType
from ua_parser import user_agent_parser

# Import security module
from security import init_security, require_admin

# Import OIDC provider
from oidc_provider import OIDCProvider, jwt_verification_required, validate_token

app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())

# OIDC Configuration (for external OIDC client)
app.config["OIDC_CLIENT_ID"] = os.environ.get("OIDC_CLIENT_ID", "")
app.config["OIDC_CLIENT_SECRET"] = os.environ.get("OIDC_CLIENT_SECRET", "")
app.config["OIDC_DISCOVERY_URL"] = os.environ.get("OIDC_DISCOVERY_URL", "")
app.config["OIDC_ALLOWED_EMAILS"] = os.environ.get("OIDC_ALLOWED_EMAILS", "").split(",")
app.config["OIDC_ADMIN_ROLES"] = os.environ.get(
    "OIDC_ADMIN_ROLES", "admin,superuser"
).split(",")

db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize security features (headers, rate limiting, input validation, logging, RBAC)
limiter = init_security(app)

# Initialise OIDC provider (for acting as OIDC server)
oidc = OIDCProvider(app)

# Register a demo OIDC client (for testing/development)
oidc.register_client(
    client_id="readreceipt-admin",
    client_secret=os.environ.get("OIDC_CLIENT_SECRET", "admin-secret"),
    redirect_uris=["http://localhost:3000/callback", "http://localhost:8080/callback"],
    grant_types=["authorization_code", "refresh_token"],
)

# OAuth setup (for acting as OIDC client to external providers)
oauth = OAuth(app)
if app.config["OIDC_DISCOVERY_URL"]:
    oauth.register(
        name="oidc",
        client_id=app.config["OIDC_CLIENT_ID"],
        client_secret=app.config["OIDC_CLIENT_SECRET"],
        server_metadata_url=app.config["OIDC_DISCOVERY_URL"],
        client_kwargs={
            "scope": "openid email profile",
        },
    )


class Recipients(db.Model):  # type: ignore[name-defined]
    id = db.Column("recipient_id", db.Integer, primary_key=True)
    r_uuid = db.Column(db.String(36))
    description = db.Column(db.String(200))
    email = db.Column(db.String(100))

    def __repr__(self) -> str:
        return f"<Recipients {self.r_uuid}>"


class Tracking(db.Model):  # type: ignore[name-defined]
    id = db.Column("tracking_id", db.Integer, primary_key=True)
    recipients_id = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    ip_country = db.Column("IPCountry", CountryType)
    connecting_ip = db.Column("ConnectingIP", IPAddressType)
    user_agent = db.Column(db.String(255))
    details = db.Column(db.JSON)

    def __repr__(self) -> str:
        return f"<Tracking {self.id}>"


class AdminUser(db.Model):  # type: ignore[name-defined]
    """Store admin users with roles mapped from OIDC claims."""

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    oidc_sub = db.Column(
        db.String(255), unique=True, nullable=False, index=True
    )  # Subject from OIDC
    roles = db.Column(
        db.JSON, default=list
    )  # List of roles: ['admin', 'superuser', etc.]
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(
        db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    last_login = db.Column(db.DateTime)
    ip_blocklist = db.Column(
        db.JSON, default=list
    )  # List of blocked IP addresses (IPv4 and IPv6)

    def __repr__(self) -> str:
        return f"<AdminUser {self.email}>"

    def has_role(self, role: str) -> bool:
        """Check if user has a specific role."""
        return role in self.roles

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "email": self.email,
            "roles": self.roles,
            "is_active": self.is_active,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            "ip_blocklist": self.ip_blocklist or [],
        }


class AuditLog(db.Model):  # type: ignore[name-defined]
    """Audit log for tracking role changes and admin actions."""

    id = db.Column(db.Integer, primary_key=True)
    admin_user_id = db.Column(db.Integer, db.ForeignKey("admin_user.id"), nullable=True)
    action = db.Column(
        db.String(100), nullable=False
    )  # e.g., 'role_added', 'role_removed', 'login', 'logout'
    details = db.Column(db.JSON)  # Additional context about the action
    ip_address = db.Column(db.String(45))  # IPv6 compatible
    user_agent = db.Column(db.String(255))
    timestamp = db.Column(db.DateTime, default=datetime.utcnow, index=True)

    admin_user = db.relationship(
        "AdminUser", backref=db.backref("audit_logs", lazy="dynamic")
    )

    def __repr__(self) -> str:
        return f"<AuditLog {self.id} - {self.action}>"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for API responses."""
        return {
            "id": self.id,
            "admin_user_id": self.admin_user_id,
            "admin_email": self.admin_user.email if self.admin_user else None,
            "action": self.action,
            "details": self.details,
            "ip_address": self.ip_address,
            "timestamp": self.timestamp.isoformat() if self.timestamp else None,
        }


def nocache(view: Callable) -> Callable:
    @wraps(view)
    def no_cache(*args: Any, **kwargs: Any) -> Any:
        response = make_response(view(*args, **kwargs))
        response.headers["Last-Modified"] = datetime.now()
        response.headers["Cache-Control"] = (
            "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        )
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return update_wrapper(no_cache, view)


def log_audit(
    admin_user: AdminUser | None, action: str, details: dict[str, Any] | None = None
) -> None:
    """Log an audit event for admin actions."""
    audit_entry = AuditLog(
        admin_user_id=admin_user.id if admin_user else None,
        action=action,
        details=details or {},
        ip_address=request.remote_addr,
        user_agent=request.headers.get("User-Agent"),
    )
    db.session.add(audit_entry)
    db.session.commit()


def extract_claims_from_token(token: dict[str, Any]) -> dict[str, Any]:
    """Extract relevant claims from OIDC token."""
    return {
        "sub": token.get("sub"),
        "email": token.get("email"),
        "email_verified": token.get("email_verified", False),
        "name": token.get("name"),
        "roles": token.get("roles", []),
        "groups": token.get("groups", []),
        "iss": token.get("iss"),
        "aud": token.get("aud"),
    }


def map_claims_to_admin_roles(claims: dict[str, Any]) -> list[str]:
    """Map OIDC claims to admin roles based on configuration.

    This function checks:
    1. Explicit role claims (e.g., 'roles', 'groups')
    2. Email whitelist for automatic admin access
    3. Custom claim mappings
    """
    roles = []

    # Check explicit role claims
    token_roles = claims.get("roles", [])
    if isinstance(token_roles, str):
        token_roles = [token_roles]

    admin_roles_config = app.config["OIDC_ADMIN_ROLES"]
    for role in token_roles:
        if role in admin_roles_config:
            roles.append(role)

    # Check groups
    token_groups = claims.get("groups", [])
    if isinstance(token_groups, str):
        token_groups = [token_groups]

    for group in token_groups:
        # Map groups to roles (e.g., "admins" group -> "admin" role)
        if group.lower() in ["admins", "administrators", "admin-group"]:
            if "admin" not in roles:
                roles.append("admin")
        if group.lower() in ["superusers", "super-admins"]:
            if "superuser" not in roles:
                roles.append("superuser")

    # Check email whitelist
    allowed_emails = app.config["OIDC_ALLOWED_EMAILS"]
    email = claims.get("email")
    if email and email in allowed_emails:
        if "admin" not in roles:
            roles.append("admin")

    return roles


def get_or_create_admin_from_claims(claims: dict[str, Any]) -> AdminUser | None:
    """Get existing admin user or create new one from OIDC claims."""
    email = claims.get("email")
    oidc_sub = claims.get("sub")

    if not email or not oidc_sub:
        return None

    # Check if user exists
    admin_user = AdminUser.query.filter_by(oidc_sub=oidc_sub).first()

    if admin_user:
        # Update roles from claims
        new_roles = map_claims_to_admin_roles(claims)
        old_roles = admin_user.roles or []

        # Log role changes
        added_roles = set(new_roles) - set(old_roles)
        removed_roles = set(old_roles) - set(new_roles)

        if added_roles:
            log_audit(admin_user, "roles_added", {"roles": list(added_roles)})
        if removed_roles:
            log_audit(admin_user, "roles_removed", {"roles": list(removed_roles)})

        admin_user.roles = new_roles
        admin_user.email = email
        admin_user.updated_at = datetime.utcnow()
    else:
        # Create new admin user
        admin_user = AdminUser(
            email=email,
            oidc_sub=oidc_sub,
            roles=map_claims_to_admin_roles(claims),
        )
        db.session.add(admin_user)
        log_audit(admin_user, "user_created", {"claims": claims})

    db.session.commit()
    return admin_user


def admin_required(f: Callable) -> Callable:
    """Decorator to require admin authentication via OIDC or fallback token."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        # Check for OIDC session
        if "oidc_user" in session:
            admin_user = AdminUser.query.get(session["oidc_user"]["id"])
            if admin_user and admin_user.is_active and admin_user.roles:
                # Update last login
                admin_user.last_login = datetime.utcnow()
                db.session.commit()
                request.current_admin_user = admin_user
                return f(*args, **kwargs)

        # Fallback to token-based auth (for backward compatibility)
        auth_header = request.headers.get("Authorization")
        expected_token = os.environ.get("ADMIN_TOKEN", "admin")
        use_oidc_only = os.environ.get("OIDC_ONLY", "false").lower() == "true"

        if use_oidc_only and not app.config["OIDC_DISCOVERY_URL"]:
            return make_response(
                json.jsonify(
                    {
                        "error": "Unauthorized",
                        "message": "OIDC authentication required but not configured",
                    }
                ),
                401,
            )

        if not auth_header:
            return make_response(
                json.jsonify(
                    {"error": "Unauthorized", "message": "Missing Authorization header"}
                ),
                401,
            )

        if auth_header != f"Bearer {expected_token}":
            return make_response(
                json.jsonify({"error": "Forbidden", "message": "Invalid token"}), 403
            )

        return f(*args, **kwargs)

    return decorated


@app.route("/")
def root_path() -> str:
    return ""


@app.route("/new-uuid")
def new_uuid() -> str:
    this_uuid = str(uuid.uuid4())
    
    # Get and validate parameters (Issue #107)
    description = request.args.get("description", "")
    email = request.args.get("email", "")
    
    # Validate email format
    if email:
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        import re
        if not re.match(email_pattern, email) or len(email) > 254:
            return json.jsonify({"error": "Invalid email format"}), 400
    
    # Sanitize and limit description length (Issue #107)
    import bleach
    if description:
        description = bleach.clean(description, tags=[], strip=True)
        if len(description) > 500:
            description = description[:497] + "..."
    
    # Create recipient with validated data
    entry = Recipients(
        r_uuid=this_uuid, 
        description=description or "", 
        email=email or ""
    )

    r = f"""
    <p>{this_uuid}<p>

    {description or ""} {email or ""}
    """
    db.session.add(entry)
    db.session.commit()
    return r


@app.route("/img/<this_uuid>")
@nocache
def send_img(this_uuid: str) -> Any:
    r_model = Recipients.query.filter_by(r_uuid=this_uuid).first()

    if r_model is None:
        return json.jsonify({"error": "Recipient not found"}), 404

    # Get the requesting IP address from headers (supports proxies)
    # Check X-Forwarded-For header first (for proxied requests)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For can contain multiple IPs, take the first one
        requesting_ip = forwarded_for.split(",")[0].strip()
    else:
        requesting_ip = request.remote_addr

    # Issue #151: IP-based own-open filtering
    # Check if requesting IP is in any admin user's blocklist
    ip_blocked = False
    admin_users = AdminUser.query.filter(AdminUser.ip_blocklist != None).all()
    for admin_user in admin_users:
        if admin_user.ip_blocklist and requesting_ip in admin_user.ip_blocklist:
            ip_blocked = True
            app.logger.info(
                f"IP-based filtering: Blocked tracking for UUID {this_uuid[:8]}... "
                f"- IP {requesting_ip} is in blocklist for user {admin_user.email}"
            )
            # Log audit event for IP block
            log_audit(
                admin_user, 
                "ip_block_triggered", 
                {"blocked_ip": requesting_ip, "uuid": this_uuid}
            )
            break

    # Build details with sanitized data (Issue #107, #108)
    details: dict[str, Any] = {}
    
    # Safely get user agent with length limit
    user_agent = request.headers.get("User-Agent", "")[:512]
    details["user_agent"] = user_agent
    
    # Sanitize headers - remove sensitive data (Issue #108)
    safe_headers = {}
    sensitive_headers = [
        "authorization", "cookie", "set-cookie", "x-api-key", 
        "x-auth-token", "cf-connecting-ip", "x-forwarded-for"
    ]
    for header_name, header_value in request.headers:
        header_lower = header_name.lower()
        if header_lower not in sensitive_headers:
            # Truncate long header values
            safe_headers[header_name] = header_value[:1024]
    details["headers"] = safe_headers
    
    # Don't log raw remote_addr in details (it's already in access logs)
    details["remote_addr"] = "***REDACTED***"
    
    # Sanitize referrer
    referrer = request.referrer
    if referrer:
        # Truncate and sanitize referrer
        details["referrer"] = referrer[:512] if len(referrer) <= 512 else referrer[:509] + "..."
    else:
        details["referrer"] = None
    
    # Only store safe query parameters
    safe_values = {}
    for key, value in request.values.items():
        if key.lower() not in ["token", "password", "secret", "email"]:
            safe_values[key] = str(value)[:256]
    details["values"] = safe_values
    
    details["date"] = datetime.now().isoformat()

    # Log tracking event safely (Issue #108)
    app.logger.info(f"Tracking event for UUID: {this_uuid[:8]}... from {requesting_ip}")

    img_io = io.BytesIO()
    img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    img.save(img_io, format="PNG")
    img_io.seek(0)

    ua = user_agent_parser.Parse(details["user_agent"])

    # Issue #150: Cookie-based own-open filtering
    # Check if rr_ignore_me cookie is present - if so, skip tracking
    rr_ignore_me = request.cookies.get("rr_ignore_me")
    if rr_ignore_me:
        app.logger.info(f"Skipping tracking for UUID {this_uuid[:8]}... - rr_ignore_me cookie present")

    # Only record tracking if:
    # 1. Not Gmail's proxy (existing check)
    # 2. rr_ignore_me cookie is NOT present (Issue #150)
    # 3. Requesting IP is NOT in any admin's blocklist (Issue #151)
    if (
        not ua["user_agent"]["family"] == "GmailImageProxy" 
        and not rr_ignore_me 
        and not ip_blocked
    ):
        entry = Tracking(
            recipients_id=r_model.id,
            timestamp=datetime.now(),
            ip_country=request.headers.get("Cf-Ipcountry"),
            connecting_ip=requesting_ip,
            user_agent=details["user_agent"],
            details=json.dumps(details),
        )
        db.session.add(entry)
        db.session.commit()
    else:
        app.logger.info(
            f"Tracking skipped for UUID {this_uuid[:8]}... - "
            f"GmailProxy={ua['user_agent']['family'] == 'GmailImageProxy'}, "
            f"Cookie={rr_ignore_me is not None}, IPBlocked={ip_blocked}"
        )

    return send_file(img_io, download_name="1.png", mimetype="image/png")  # type: ignore[call-arg]


# ============================================================================
# OIDC Authentication Endpoints
# ============================================================================


@app.route("/api/auth/login")
def oidc_login() -> Any:
    """Initiate OIDC login flow."""
    if not app.config["OIDC_DISCOVERY_URL"]:
        return json.jsonify(
            {"error": "OIDC not configured", "message": "OIDC discovery URL not set"}
        ), 503

    redirect_uri = url_for("oidc_callback", _external=True)
    return oauth.oidc.authorize_redirect(redirect_uri)


@app.route("/api/auth/callback")
def oidc_callback() -> Any:
    """Handle OIDC callback after authentication."""
    if not app.config["OIDC_DISCOVERY_URL"]:
        return json.jsonify(
            {"error": "OIDC not configured", "message": "OIDC discovery URL not set"}
        ), 503

    try:
        token = oauth.oidc.authorize_access_token()
    except Exception as e:
        app.logger.error(f"OIDC token exchange failed: {e}")
        return json.jsonify(
            {
                "error": "Authentication failed",
                "message": "Could not complete OIDC authentication",
            }
        ), 400

    # Extract claims from token
    claims = extract_claims_from_token(token.get("userinfo", token))

    # Validate email
    email = claims.get("email")
    if not email:
        return json.jsonify(
            {"error": "Unauthorized", "message": "Email claim not found in token"}
        ), 403

    # Check email whitelist if configured
    allowed_emails = app.config["OIDC_ALLOWED_EMAILS"]
    if allowed_emails and email not in allowed_emails:
        log_audit(
            None, "login_denied", {"email": email, "reason": "email_not_whitelisted"}
        )
        return json.jsonify(
            {"error": "Forbidden", "message": "Email not in allowed list"}
        ), 403

    # Map claims to admin roles and get/create user
    admin_user = get_or_create_admin_from_claims(claims)

    if not admin_user or not admin_user.roles:
        log_audit(
            admin_user, "login_denied", {"email": email, "reason": "no_admin_roles"}
        )
        return json.jsonify(
            {"error": "Forbidden", "message": "User does not have admin roles"}
        ), 403

    # Store user in session
    session["oidc_user"] = {
        "id": admin_user.id,
        "email": admin_user.email,
        "roles": admin_user.roles,
    }

    # Update last login
    admin_user.last_login = datetime.utcnow()
    db.session.commit()

    # Log successful login
    log_audit(admin_user, "login", {"claims": claims})

    # Redirect to dashboard or return JSON for API clients
    if request.headers.get("Accept") == "application/json":
        return json.jsonify(
            {
                "status": "authenticated",
                "user": admin_user.to_dict(),
            }
        ), 200

    return redirect("/admin/dashboard")


@app.route("/api/auth/logout", methods=["POST", "GET"])
def oidc_logout() -> Any:
    """Logout and clear session."""
    admin_user = None
    if "oidc_user" in session:
        admin_user = AdminUser.query.get(session["oidc_user"]["id"])
        if admin_user:
            log_audit(admin_user, "logout", {})

    session.clear()

    if request.headers.get("Accept") == "application/json":
        return json.jsonify({"status": "logged_out"}), 200

    return redirect("/")


@app.route("/api/auth/me")
def get_current_user() -> Any:
    """Get current authenticated user info."""
    if "oidc_user" in session:
        admin_user = AdminUser.query.get(session["oidc_user"]["id"])
        if admin_user:
            return json.jsonify(
                {
                    "authenticated": True,
                    "user": admin_user.to_dict(),
                }
            ), 200

    # Check for token auth
    auth_header = request.headers.get("Authorization")
    if auth_header:
        expected_token = os.environ.get("ADMIN_TOKEN", "admin")
        if auth_header == f"Bearer {expected_token}":
            return json.jsonify(
                {
                    "authenticated": True,
                    "user": {
                        "email": "token-admin",
                        "roles": ["admin"],
                        "auth_type": "token",
                    },
                }
            ), 200

    return json.jsonify({"authenticated": False}), 401


# ============================================================================
# Legacy Token Authentication (for backward compatibility)
# ============================================================================


@app.route("/api/admin/login", methods=["POST"])
def admin_login() -> Any:
    """Admin login endpoint with token authentication."""
    # Validate request data (Issue #107)
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data or "token" not in data:
        return json.jsonify({"error": "Token is required"}), 400
    
    token = data.get("token")
    
    # Validate token format (Issue #107)
    if not isinstance(token, str) or len(token) > 1024:
        return json.jsonify({"error": "Invalid token format"}), 400

    admin_token = os.environ.get("ADMIN_TOKEN", "admin")
    use_oidc_only = os.environ.get("OIDC_ONLY", "false").lower() == "true"

    if use_oidc_only and app.config["OIDC_DISCOVERY_URL"]:
        return json.jsonify(
            {
                "error": "Token auth disabled",
                "message": "OIDC-only mode enabled. Use /api/auth/login",
            }
        ), 403

    if token == admin_token:
        # Audit successful login (Issue #109)
        log_audit(None, "token_login", {"method": "token", "ip": request.remote_addr})
        app.logger.info(
            f"AUDIT: Admin login successful from {request.remote_addr}"
        )
        return json.jsonify({
            "status": "authenticated",
            "auth_type": "token",
        }), 200
    
    # Log failed login attempt (Issue #109)
    app.logger.warning(
        f"AUDIT: Failed admin login attempt from {request.remote_addr}"
    )

    return json.jsonify({"error": "Invalid token"}), 401


# ============================================================================
# OIDC Token Endpoints (for OIDC provider integration)
# ============================================================================

@app.route("/api/admin/oidc/login", methods=["POST"])
def admin_oidc_login() -> Any:
    """Admin login endpoint with OIDC token authentication."""
    data = request.get_json()
    access_token = data.get("access_token")

    if not access_token:
        return json.jsonify({"error": "access_token is required"}), 400

    # Validate the OIDC token
    payload = validate_token(access_token, oidc)
    if payload is None:
        return json.jsonify({"error": "Invalid or expired token"}), 401

    return json.jsonify(
        {
            "status": "authenticated",
            "user": {
                "sub": payload.get("sub"),
                "scope": payload.get("scope"),
            },
        }
    ), 200


@app.route("/api/admin/protected", methods=["GET"])
@jwt_verification_required(oidc)
def admin_protected() -> Any:
    """Protected admin endpoint requiring valid OIDC token."""
    # Access the decoded JWT payload from request context
    payload = request.oidc_payload  # type: ignore[attr-defined]
    return json.jsonify(
        {
            "status": "access_granted",
            "message": "Welcome to the protected area",
            "user": {
                "sub": payload.get("sub"),
                "scope": payload.get("scope"),
            },
        }
    ), 200


# ============================================================================
# Admin User Management Endpoints
# ============================================================================


@app.route("/api/admin/users", methods=["GET"])
@admin_required
def get_admin_users() -> Any:
    """Get all admin users."""
    users = AdminUser.query.all()
    return json.jsonify(
        {
            "users": [user.to_dict() for user in users],
            "total": len(users),
        }
    ), 200


@app.route("/api/admin/users/<int:user_id>", methods=["GET"])
@admin_required
def get_admin_user(user_id: int) -> Any:
    """Get a specific admin user."""
    user = AdminUser.query.get_or_404(user_id)
    return json.jsonify(user.to_dict()), 200


@app.route("/api/admin/users/<int:user_id>/roles", methods=["PUT"])
@admin_required
def update_admin_user_roles(user_id: int) -> Any:
    """Update admin user roles."""
    user = AdminUser.query.get_or_404(user_id)
    data = request.get_json()

    if not data or "roles" not in data:
        return json.jsonify({"error": "roles field required"}), 400

    new_roles = data["roles"]
    if not isinstance(new_roles, list):
        return json.jsonify({"error": "roles must be a list"}), 400

    old_roles = user.roles or []
    added_roles = set(new_roles) - set(old_roles)
    removed_roles = set(old_roles) - set(new_roles)

    # Prevent removing all roles from last admin
    if not new_roles:
        admin_count = AdminUser.query.filter(
            AdminUser.roles != [], AdminUser.is_active
        ).count()
        if admin_count <= 1:
            return json.jsonify(
                {"error": "Cannot remove all roles from last admin"}
            ), 400

    user.roles = new_roles
    user.updated_at = datetime.utcnow()
    db.session.commit()

    # Log the changes
    current_admin = getattr(request, "current_admin_user", None)
    if added_roles:
        log_audit(
            current_admin,
            "roles_added_by_admin",
            {
                "target_user": user.email,
                "roles": list(added_roles),
            },
        )
    if removed_roles:
        log_audit(
            current_admin,
            "roles_removed_by_admin",
            {
                "target_user": user.email,
                "roles": list(removed_roles),
            },
        )

    return json.jsonify(user.to_dict()), 200


@app.route("/api/admin/users/<int:user_id>/activate", methods=["POST"])
@admin_required
def activate_admin_user(user_id: int) -> Any:
    """Activate an admin user."""
    user = AdminUser.query.get_or_404(user_id)
    user.is_active = True
    user.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit(
        getattr(request, "current_admin_user", None),
        "user_activated",
        {"target_user": user.email},
    )

    return json.jsonify(user.to_dict()), 200


@app.route("/api/admin/users/<int:user_id>/deactivate", methods=["POST"])
@admin_required
def deactivate_admin_user(user_id: int) -> Any:
    """Deactivate an admin user."""
    user = AdminUser.query.get_or_404(user_id)

    # Prevent deactivating last admin
    admin_count = AdminUser.query.filter(
        AdminUser.roles != [], AdminUser.is_active, AdminUser.id != user_id
    ).count()
    if admin_count == 0:
        return json.jsonify({"error": "Cannot deactivate last active admin"}), 400

    user.is_active = False
    user.updated_at = datetime.utcnow()
    db.session.commit()

    log_audit(
        getattr(request, "current_admin_user", None),
        "user_deactivated",
        {"target_user": user.email},
    )

    return json.jsonify(user.to_dict()), 200


@app.route("/api/admin/audit-logs", methods=["GET"])
@admin_required
def get_audit_logs() -> Any:
    """Get audit logs with optional filtering."""
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 50, type=int)
    action = request.args.get("action")
    user_id = request.args.get("user_id", type=int)

    query = AuditLog.query.order_by(AuditLog.timestamp.desc())

    if action:
        query = query.filter_by(action=action)
    if user_id:
        query = query.filter_by(admin_user_id=user_id)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)

    return json.jsonify(
        {
            "logs": [log.to_dict() for log in pagination.items],
            "total": pagination.total,
            "pages": pagination.pages,
            "current_page": page,
            "per_page": per_page,
        }
    ), 200


# ============================================================================
# Legacy Admin Endpoints (now protected with admin_required)
# ============================================================================


@app.route("/api/admin/recipients", methods=["GET"])
@require_admin
def get_recipients() -> Any:
    """Get all recipients."""
    recipients = Recipients.query.all()
    return (
        json.jsonify(
            [
                {
                    "id": r.id,
                    "r_uuid": r.r_uuid,
                    "description": r.description,
                    "email": r.email,
                }
                for r in recipients
            ]
        ),
        200,
    )


@app.route("/api/admin/recipients", methods=["POST"])
@require_admin
def create_recipient() -> Any:
    """Create a new recipient."""
    # Validate input (Issue #107)
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return json.jsonify({"error": "Request body is required"}), 400

    if not data.get("email"):
        return json.jsonify({"error": "Email is required"}), 400
    
    # Validate email format (Issue #107)
    import re
    email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
    if not re.match(email_pattern, data["email"]) or len(data["email"]) > 254:
        return json.jsonify({"error": "Invalid email format"}), 400
    
    # Sanitize description (Issue #107)
    import bleach
    description = data.get("description", "")
    if description:
        description = bleach.clean(description, tags=[], strip=True)
        if len(description) > 500:
            description = description[:497] + "..."
        data["description"] = description

    recipient = Recipients(
        r_uuid=str(uuid.uuid4()),
        description=description,
        email=data["email"][:254],  # Limit email length
    )
    db.session.add(recipient)
    db.session.commit()

    # Audit creation (Issue #109)
    app.logger.info(
        f"AUDIT: Recipient created - email: {data['email'][:3]}*** by admin"
    )

    return (
        json.jsonify(
            {
                "id": recipient.id,
                "r_uuid": recipient.r_uuid,
                "description": recipient.description,
                "email": recipient.email,
            }
        ),
        201,
    )


@app.route("/api/admin/recipients/<int:recipient_id>", methods=["PUT"])
@require_admin
def update_recipient(recipient_id: int) -> Any:
    """Update a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
    
    # Validate input (Issue #107)
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return json.jsonify({"error": "Request body is required"}), 400
    
    import re
    import bleach
    
    if "description" in data:
        # Sanitize description
        description = bleach.clean(str(data["description"]), tags=[], strip=True)
        recipient.description = description[:500]
    
    if "email" in data:
        # Validate email format
        email = data["email"]
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", email):
            return json.jsonify({"error": "Invalid email format"}), 400
        recipient.email = email[:254]

    db.session.commit()
    
    # Audit update (Issue #109)
    app.logger.info(f"AUDIT: Recipient {recipient_id} updated by admin")

    return (
        json.jsonify(
            {
                "id": recipient.id,
                "r_uuid": recipient.r_uuid,
                "description": recipient.description,
                "email": recipient.email,
            }
        ),
        200,
    )


@app.route("/api/admin/recipients/<int:recipient_id>", methods=["DELETE"])
@require_admin
def delete_recipient(recipient_id: int) -> Any:
    """Delete a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
    
    # Store ID for audit log before deletion
    recipient_uuid = recipient.r_uuid
    
    db.session.delete(recipient)
    db.session.commit()
    
    # Audit deletion (Issue #109)
    app.logger.info(f"AUDIT: Recipient {recipient_uuid} deleted by admin")

    return json.jsonify({"status": "deleted"}), 200


@app.route("/api/admin/stats", methods=["GET"])
@require_admin
def get_admin_stats() -> Any:
    """Get dashboard statistics."""
    total_recipients = Recipients.query.count()
    total_events = Tracking.query.count()

    yesterday = datetime.now() - timedelta(days=1)
    events_today = Tracking.query.filter(Tracking.timestamp >= yesterday).count()

    recent_events = Tracking.query.order_by(Tracking.timestamp.desc()).limit(5).all()

    return (
        json.jsonify(
            {
                "total_recipients": total_recipients,
                "total_events": total_events,
                "events_today": events_today,
                "unique_opens": Tracking.query.distinct(Tracking.recipients_id).count(),
                "recent_events": [
                    {
                        "id": event.id,
                        "timestamp": (
                            event.timestamp.isoformat() if event.timestamp else None
                        ),
                    }
                    for event in recent_events
                ],
            }
        ),
        200,
    )


@app.route("/api/admin/settings", methods=["GET"])
@require_admin
def get_settings() -> Any:
    """Get application settings."""
    return (
        json.jsonify(
            {
                "tracking_enabled": True,
                "allowed_domains": os.environ.get("EXTENSION_ALLOWED_ORIGINS", ""),
                "log_level": os.environ.get("LOG_LEVEL", "INFO"),
                "cookie_filtering_enabled": os.environ.get("COOKIE_FILTERING_ENABLED", "true").lower() == "true",
            }
        ),
        200,
    )


@app.route("/api/admin/settings", methods=["PUT"])
@require_admin
def update_settings() -> Any:
    """Update application settings (in-memory for now)."""
    # Validate input (Issue #107)
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data:
        return json.jsonify({"error": "Request body is required"}), 400
    
    # Sanitize values
    import bleach
    safe_data = {}
    for key, value in data.items():
        if isinstance(value, str):
            safe_data[key] = bleach.clean(value, tags=[], strip=True)[:500]
        else:
            safe_data[key] = value
    
    # Audit settings change (Issue #109)
    app.logger.info(f"AUDIT: Settings updated by admin - keys: {list(safe_data.keys())}")
    
    return json.jsonify({"status": "updated", "settings": safe_data}), 200


# ============================================================================
# IP Blocklist Management Endpoints (Issue #151)
# ============================================================================

@app.route("/api/admin/ip-blocklist", methods=["GET"])
@admin_required
def get_ip_blocklist() -> Any:
    """Get the current user's IP blocklist."""
    admin_user = getattr(request, "current_admin_user", None)
    if not admin_user:
        return json.jsonify({"error": "Admin user not found"}), 404
    
    return json.jsonify({
        "ip_blocklist": admin_user.ip_blocklist or [],
        "count": len(admin_user.ip_blocklist or [])
    }), 200


@app.route("/api/admin/ip-blocklist", methods=["POST"])
@admin_required
def add_to_ip_blocklist() -> Any:
    """Add an IP address to the blocklist."""
    admin_user = getattr(request, "current_admin_user", None)
    if not admin_user:
        return json.jsonify({"error": "Admin user not found"}), 404
    
    # Validate request data
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data or "ip_address" not in data:
        return json.jsonify({"error": "ip_address is required"}), 400
    
    ip_address = data["ip_address"].strip()
    
    # Validate IP address format (IPv4 or IPv6)
    import ipaddress
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return json.jsonify({"error": "Invalid IP address format"}), 400
    
    # Initialize blocklist if None
    if admin_user.ip_blocklist is None:
        admin_user.ip_blocklist = []
    
    # Check if IP already in blocklist
    if ip_address in admin_user.ip_blocklist:
        return json.jsonify({"error": "IP address already in blocklist"}), 409
    
    # Add IP to blocklist
    admin_user.ip_blocklist.append(ip_address)
    admin_user.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Audit the change
    log_audit(
        admin_user,
        "ip_blocklist_add",
        {"ip_address": ip_address, "total_blocked": len(admin_user.ip_blocklist)}
    )
    
    app.logger.info(
        f"AUDIT: IP {ip_address} added to blocklist by {admin_user.email}"
    )
    
    return json.jsonify({
        "status": "added",
        "ip_address": ip_address,
        "total_blocked": len(admin_user.ip_blocklist)
    }), 201


@app.route("/api/admin/ip-blocklist/<ip_address>", methods=["DELETE"])
@admin_required
def remove_from_ip_blocklist(ip_address: str) -> Any:
    """Remove an IP address from the blocklist."""
    admin_user = getattr(request, "current_admin_user", None)
    if not admin_user:
        return json.jsonify({"error": "Admin user not found"}), 404
    
    # Validate IP address format
    import ipaddress
    try:
        ipaddress.ip_address(ip_address)
    except ValueError:
        return json.jsonify({"error": "Invalid IP address format"}), 400
    
    # Initialize blocklist if None
    if admin_user.ip_blocklist is None:
        admin_user.ip_blocklist = []
    
    # Check if IP is in blocklist
    if ip_address not in admin_user.ip_blocklist:
        return json.jsonify({"error": "IP address not in blocklist"}), 404
    
    # Remove IP from blocklist
    admin_user.ip_blocklist.remove(ip_address)
    admin_user.updated_at = datetime.utcnow()
    db.session.commit()
    
    # Audit the change
    log_audit(
        admin_user,
        "ip_blocklist_remove",
        {"ip_address": ip_address, "total_blocked": len(admin_user.ip_blocklist)}
    )
    
    app.logger.info(
        f"AUDIT: IP {ip_address} removed from blocklist by {admin_user.email}"
    )
    
    return json.jsonify({
        "status": "removed",
        "ip_address": ip_address,
        "total_blocked": len(admin_user.ip_blocklist)
    }), 200


@app.route("/api/admin/ip-blocklist/validate", methods=["POST"])
@admin_required
def validate_ip_address() -> Any:
    """Validate an IP address format without adding to blocklist."""
    if not request.is_json:
        return json.jsonify({"error": "Content-Type must be application/json"}), 400
    
    data = request.get_json()
    if not data or "ip_address" not in data:
        return json.jsonify({"error": "ip_address is required"}), 400
    
    ip_address = data["ip_address"].strip()
    
    # Validate IP address format
    import ipaddress
    try:
        parsed = ipaddress.ip_address(ip_address)
        ip_version = "IPv6" if parsed.version == 6 else "IPv4"
        return json.jsonify({
            "valid": True,
            "ip_address": ip_address,
            "version": ip_version,
            "normalized": str(parsed)
        }), 200
    except ValueError:
        return json.jsonify({
            "valid": False,
            "error": "Invalid IP address format. Use IPv4 (e.g., 192.168.1.1) or IPv6 (e.g., 2001:db8::1)"
        }), 400


@app.route("/api/analytics/summary", methods=["GET"])
@require_admin
def get_analytics_summary() -> Any:
    """Get analytics summary."""
    total_events = Tracking.query.count()
    unique_recipients = Tracking.query.distinct(Tracking.recipients_id).count()

    last_week = datetime.now() - timedelta(days=7)
    events_last_week = Tracking.query.filter(Tracking.timestamp >= last_week).count()
    avg_daily = events_last_week / 7 if events_last_week > 0 else 0

    top_country = (
        db.session.query(Tracking.ip_country, db.func.count(Tracking.id))
        .group_by(Tracking.ip_country)
        .order_by(db.func.count(Tracking.id).desc())
        .first()
    )

    return (
        json.jsonify(
            {
                "total_events": total_events,
                "unique_recipients": unique_recipients,
                "avg_daily_opens": round(avg_daily, 2),
                "top_country": top_country[0] if top_country else None,
            }
        ),
        200,
    )


@app.route("/api/analytics/events", methods=["GET"])
@require_admin
def get_analytics_events() -> Any:
    """Get time-series event data."""
    # Validate and sanitize range parameter (Issue #107)
    range_days = request.args.get("range", "7d")
    
    # Validate format - only allow digits followed by 'd'
    import re
    if not re.match(r"^\d+d$", range_days):
        return json.jsonify({"error": "Invalid range format. Use format like '7d', '30d'"}), 400
    
    days = int(range_days.replace("d", ""))
    
    # Limit range to prevent abuse (max 365 days)
    if days > 365 or days < 1:
        return json.jsonify({"error": "Range must be between 1 and 365 days"}), 400
    
    start_date = datetime.now() - timedelta(days=days)

    events = Tracking.query.filter(Tracking.timestamp >= start_date).all()

    daily_counts: dict[str, int] = {}
    for event in events:
        date_str = event.timestamp.strftime("%Y-%m-%d") if event.timestamp else None
        if date_str:
            daily_counts[date_str] = daily_counts.get(date_str, 0) + 1

    return (
        json.jsonify(
            [
                {"date": date, "count": count}
                for date, count in sorted(daily_counts.items())
            ]
        ),
        200,
    )


@app.route("/api/analytics/recipients", methods=["GET"])
@require_admin
def get_analytics_recipients() -> Any:
    """Get top recipients by opens."""
    top_recipients = (
        db.session.query(Tracking.recipients_id, db.func.count(Tracking.id))
        .group_by(Tracking.recipients_id)
        .order_by(db.func.count(Tracking.id).desc())
        .limit(10)
        .all()
    )

    return (
        json.jsonify(
            [{"recipient_id": rid, "count": count} for rid, count in top_recipients]
        ),
        200,
    )


@app.route("/api/analytics/geo", methods=["GET"])
@require_admin
def get_analytics_geo() -> Any:
    """Get geographic distribution."""
    geo_data = (
        db.session.query(Tracking.ip_country, db.func.count(Tracking.id))
        .group_by(Tracking.ip_country)
        .all()
    )

    return (
        json.jsonify(
            [
                {"country": country or "Unknown", "count": count}
                for country, count in geo_data
            ]
        ),
        200,
    )


@app.route("/api/analytics/clients", methods=["GET"])
@require_admin
def get_analytics_clients() -> Any:
    """Get email client breakdown."""
    events = Tracking.query.all()
    client_counts: dict[str, int] = {}

    for event in events:
        if event.details:
            try:
                details = (
                    json.loads(event.details)
                    if isinstance(event.details, str)
                    else event.details
                )
                ua_string = details.get("user_agent", "")
                ua = user_agent_parser.Parse(ua_string)
                client = ua["user_agent"]["family"]

                if client == "GmailImageProxy":
                    client = "Gmail"
                elif client:
                    client = client.split(" ")[0]
                else:
                    client = "Unknown"

                client_counts[client] = client_counts.get(client, 0) + 1
            except Exception:
                client_counts["Unknown"] = client_counts.get("Unknown", 0) + 1

    return (
        json.jsonify(
            [
                {"name": name, "value": count}
                for name, count in sorted(
                    client_counts.items(), key=lambda x: x[1], reverse=True
                )
            ]
        ),
        200,
    )


@app.route("/api/analytics/export", methods=["GET"])
@require_admin
def export_analytics() -> Any:
    """Export analytics data as CSV."""
    events = Tracking.query.all()

    output = StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Recipient ID", "Timestamp", "Country", "User Agent"])

    for event in events:
        writer.writerow(
            [
                event.id,
                event.recipients_id,
                event.timestamp.isoformat() if event.timestamp else "",
                event.ip_country or "",
                event.user_agent or "",
            ]
        )

    output.seek(0)
    
    # Audit export (Issue #109)
    app.logger.info(f"AUDIT: Analytics export requested by admin")
    
    return (
        output.getvalue(),
        200,
        {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=analytics_export.csv",
        },
    )


# ============================================================================
# Cookie-Based Own-Open Filtering Endpoints (Issue #150)
# ============================================================================


@app.route("/api/cookie/set", methods=["POST"])
def set_ignore_cookie() -> Any:
    """Set the rr_ignore_me cookie to prevent tracking when viewing sent folder.
    
    This endpoint is called by the admin dashboard when the user enables
    cookie-based own-open filtering (Issue #150).
    """
    response = make_response(json.jsonify({"status": "cookie_set"}), 200)
    # Set cookie for 30 days, secure and httponly for security
    response.set_cookie(
        "rr_ignore_me",
        "true",
        max_age=30 * 24 * 60 * 60,  # 30 days
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
    )
    return response


@app.route("/api/cookie/clear", methods=["POST"])
def clear_ignore_cookie() -> Any:
    """Clear the rr_ignore_me cookie to re-enable tracking."""
    response = make_response(json.jsonify({"status": "cookie_cleared"}), 200)
    response.set_cookie(
        "rr_ignore_me",
        "",
        max_age=0,
        httponly=True,
        secure=request.is_secure,
        samesite="Lax",
    )
    return response
