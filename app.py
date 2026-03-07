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

from flask import Flask, g, json, make_response, request, send_file
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
db = SQLAlchemy(app)
migrate = Migrate(app, db)

# Initialize security features (headers, rate limiting, input validation, logging, RBAC)
limiter = init_security(app)

# Initialise OIDC provider
oidc = OIDCProvider(app)

# Register a demo OIDC client (for testing/development)
oidc.register_client(
    client_id="readreceipt-admin",
    client_secret=os.environ.get("OIDC_CLIENT_SECRET", "admin-secret"),
    redirect_uris=["http://localhost:3000/callback", "http://localhost:8080/callback"],
    grant_types=["authorization_code", "refresh_token"],
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
    app.logger.info(f"Tracking event for UUID: {this_uuid[:8]}... from {request.remote_addr}")

    img_io = io.BytesIO()
    img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    img.save(img_io, format="PNG")
    img_io.seek(0)

    ua = user_agent_parser.Parse(details["user_agent"])

    if not ua["user_agent"]["family"] == "GmailImageProxy":
        entry = Tracking(
            recipients_id=r_model.id,
            timestamp=datetime.now(),
            ip_country=request.headers.get("Cf-Ipcountry"),
            connecting_ip=request.headers.get("Cf-Connecting-Ip"),
            user_agent=details["user_agent"],
            details=json.dumps(details),
        )
        db.session.add(entry)
        db.session.commit()

    return send_file(img_io, download_name="1.png", mimetype="image/png")  # type: ignore[call-arg]


def admin_required(
    f: Callable,
) -> Callable:
    """Decorator to require admin authentication."""

    @wraps(f)
    def decorated(*args: Any, **kwargs: Any) -> Any:
        auth_header = request.headers.get("Authorization")
        expected_token = os.environ.get("ADMIN_TOKEN", "admin")

        if not auth_header:
            return make_response(
                {"error": "Unauthorized", "message": "Missing Authorization header"},
                401,
            )

        if auth_header != f"Bearer {expected_token}":
            return make_response(
                {"error": "Forbidden", "message": "Invalid token"}, 403
            )

        return f(*args, **kwargs)

    return decorated


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

    if token == admin_token:
        # Audit successful login (Issue #109)
        app.logger.info(
            f"AUDIT: Admin login successful from {request.remote_addr}"
        )
        return json.jsonify({"status": "authenticated"}), 200
    
    # Log failed login attempt (Issue #109)
    app.logger.warning(
        f"AUDIT: Failed admin login attempt from {request.remote_addr}"
    )
    return json.jsonify({"error": "Invalid token"}), 401


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
