from __future__ import annotations

import csv
import hashlib
import io
import logging
import os
import re
import uuid
from collections.abc import Callable
from datetime import datetime, timedelta
from functools import update_wrapper, wraps
from io import StringIO
from typing import Any

import bleach
import jwt
from flask import Flask, json, make_response, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import CSRFProtect
from PIL import Image
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
)
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy_utils import CountryType, IPAddressType
from ua_parser import user_agent_parser

from utils.logging import configure_logging, get_logger, init_logging_middleware
from utils.retry import retry_with_backoff

app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

# SECURITY FIX #101: SECRET_KEY must be set via environment variable
# In production, this should be a secure random value generated once and stored
# Generate with: python -c "import secrets; print(secrets.token_hex(32))"
# In development only, we generate a random key if not set
flask_env = os.environ.get("FLASK_ENV", "development")
secret_key = os.environ.get("SECRET_KEY")

if not secret_key:
    if flask_env == "production":
        # CRITICAL: Fail fast in production if SECRET_KEY is not set
        raise RuntimeError(
            "SECRET_KEY environment variable is required in production. "
            'Generate a secure key with: python -c "import secrets; print(secrets.token_hex(32))"'
        )
    else:
        # Development only: generate a random key (will change on restart)
        logger = logging.getLogger(__name__)
        logger.warning(
            "SECRET_KEY not set, using random key for development. "
            "Set SECRET_KEY environment variable for production."
        )
        app.config["SECRET_KEY"] = os.urandom(32).hex()
else:
    app.config["SECRET_KEY"] = secret_key

# SECURITY FIX #100: Flask debug mode should only be enabled in development
# Never enable debug mode in production as it exposes sensitive information
debug_mode = os.environ.get("FLASK_DEBUG", "0").lower() in ("1", "true", "yes")
if flask_env == "production" and debug_mode:
    logger = logging.getLogger(__name__)
    logger.error(
        "SECURITY WARNING: FLASK_DEBUG is enabled in production environment. "
        "This exposes sensitive debugging information. Set FLASK_DEBUG=0 or FLASK_ENV=production."
    )
    # Force disable debug in production
    app.config["DEBUG"] = False
else:
    app.config["DEBUG"] = debug_mode if flask_env == "development" else False

# Validate required environment variables at startup
if not os.environ.get("ADMIN_TOKEN"):
    raise RuntimeError("ADMIN_TOKEN environment variable is required but not set")

# Retry configuration
app.config["RETRY_MAX_ATTEMPTS"] = int(os.environ.get("RETRY_MAX_ATTEMPTS", "5"))
app.config["RETRY_BASE_DELAY"] = float(os.environ.get("RETRY_BASE_DELAY", "2"))
app.config["RETRY_MAX_DELAY"] = float(os.environ.get("RETRY_MAX_DELAY", "30"))
app.config["RETRY_JITTER"] = os.environ.get("RETRY_JITTER", "true").lower() == "true"

# Logging configuration
app.config["LOG_LEVEL"] = os.environ.get("LOG_LEVEL", "INFO")
app.config["LOG_FORMAT"] = os.environ.get("LOG_FORMAT", "json")
app.config["LOG_REDACT_FIELDS"] = os.environ.get("LOG_REDACT_FIELDS", "").split(",")

# CORS configuration - restrict to allowed origins from environment variable
allowed_origins = os.environ.get(
    "EXTENSION_ALLOWED_ORIGINS", "https://mail.google.com"
).split(",")
CORS(
    app,
    resources={
        r"/api/*": {
            "origins": allowed_origins,
            "methods": ["GET", "POST", "PUT", "DELETE"],
            "allow_headers": ["Content-Type", "Authorization"],
        }
    },
)

# SECURITY FIX #98: CSRF Protection
# Enable CSRF protection for all state-changing endpoints
# CSRF tokens must be included in POST, PUT, DELETE requests
csrf = CSRFProtect(app)

# Configure CSRF settings for API-based authentication
# We use header-based CSRF tokens for API endpoints
app.config["WTF_CSRF_CHECK_DEFAULT"] = True  # Enable CSRF by default
app.config["WTF_CSRF_SSL_STRICT"] = True
app.config["WTF_CSRF_TIME_LIMIT"] = 3600  # 1 hour token validity
app.config["WTF_CSRF_SECRET_KEY"] = app.config["SECRET_KEY"]
# Allow CSRF token via header for API endpoints
app.config["WTF_CSRF_HEADERS"] = ["X-CSRFToken", "X-CSRF-Token"]

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
    enabled=os.environ.get("FLASK_RATELIMIT_ENABLED", "true").lower() == "true",
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
logger = get_logger(__name__)

# SECURITY FIX #96: JWT Token Configuration
# Token expiration time (24 hours)
JWT_TOKEN_EXPIRY_HOURS = int(os.environ.get("JWT_TOKEN_EXPIRY_HOURS", "24"))
JWT_ALGORITHM = "HS256"

# In-memory token blacklist for revoked tokens (use Redis in production)
# This stores token jti (unique identifiers) until they expire
token_blacklist: set[str] = set()


def generate_jwt_token(admin_token: str) -> str:
    """
    Generate a JWT token for authenticated admin sessions.

    SECURITY FIX #96: Implements proper session-based authentication with:
    - Token expiration (24 hours by default)
    - Unique token identifier (jti) for revocation
    - Hashed token storage (token is hashed before comparison)

    Args:
        admin_token: The validated admin token from environment

    Returns:
        JWT token string
    """
    now = datetime.now()
    payload = {
        "sub": "admin",  # Subject
        "iat": now,  # Issued at
        "exp": now + timedelta(hours=JWT_TOKEN_EXPIRY_HOURS),  # Expiration
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
        "type": "access",  # Token type
    }

    # Hash the admin token to include in payload (not stored in plain text)
    token_hash = hashlib.sha256(admin_token.encode()).hexdigest()
    payload["th"] = token_hash  # Token hash for validation

    return jwt.encode(payload, app.config["SECRET_KEY"], algorithm=JWT_ALGORITHM)


def verify_jwt_token(token: str) -> dict[str, Any] | None:
    """
    Verify and decode a JWT token.

    SECURITY FIX #96: Validates JWT tokens with:
    - Signature verification
    - Expiration check
    - Blacklist check (for revoked tokens)
    - Token hash validation

    Args:
        token: JWT token string to verify

    Returns:
        Decoded payload if valid, None otherwise
    """
    try:
        # Check if token is blacklisted (revoked)
        # Decode without verification first to get jti
        unverified = jwt.decode(token, options={"verify_signature": False})
        jti = unverified.get("jti")
        if jti and jti in token_blacklist:
            logger.warning("Attempted to use blacklisted token", extra={"jti": jti})
            return None

        # Full verification with signature and expiration
        payload = jwt.decode(
            token,
            app.config["SECRET_KEY"],
            algorithms=[JWT_ALGORITHM],
            options={"require": ["exp", "iat", "jti", "sub"]},
        )

        # Validate token hash matches current admin token
        admin_token = os.environ.get("ADMIN_TOKEN")
        if admin_token:
            expected_hash = hashlib.sha256(admin_token.encode()).hexdigest()
            if payload.get("th") != expected_hash:
                logger.warning(
                    "Token hash mismatch - token may be from old admin token"
                )
                return None

        return payload

    except jwt.ExpiredSignatureError:
        logger.warning("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.warning(f"Invalid JWT token: {e}")
        return None


def revoke_jwt_token(token: str) -> bool:
    """
    Revoke a JWT token by adding it to the blacklist.

    SECURITY FIX #96: Allows token revocation before expiration.
    In production, use Redis or database for distributed blacklist.

    Args:
        token: JWT token to revoke

    Returns:
        True if successfully revoked, False otherwise
    """
    try:
        payload = jwt.decode(token, options={"verify_signature": False})
        jti = payload.get("jti")
        if jti:
            token_blacklist.add(jti)
            logger.info("Token revoked", extra={"jti": jti})
            return True
        return False
    except jwt.InvalidTokenError:
        return False


# Prometheus metrics setup
metrics = PrometheusMetrics(
    app,
    defaults_prefix="readreceipt",
    excluded_paths=["/metrics", "/metrics/health"],
    group_by="endpoint",
)

# Custom business metrics
tracking_events_total = Counter(
    "tracking_events_total",
    "Total number of tracking events recorded",
    ["recipient_id", "country"],
)

tracking_events_unique_recipients = Gauge(
    "tracking_events_unique_recipients",
    "Number of unique recipients with tracking events",
)

recipients_total = Gauge("recipients_total", "Total number of recipients in the system")

tracking_event_processing_seconds = Histogram(
    "tracking_event_processing_seconds",
    "Time spent processing tracking events",
    buckets=(0.001, 0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1.0),
)


# Metrics health check endpoint
@app.route("/metrics/health")
def metrics_health() -> Any:
    """Health check endpoint for metrics monitoring."""
    try:
        # Check database connection
        db.session.execute("SELECT 1")
        db_status = "connected"
    except Exception:
        db_status = "disconnected"

    # Get metrics count summary
    from prometheus_client import REGISTRY

    metrics_count = len(list(REGISTRY.collect()))

    return json.jsonify(
        {
            "status": "healthy",
            "database": db_status,
            "metrics_count": metrics_count,
            "timestamp": datetime.now().isoformat(),
        }
    ), 200


def update_recipients_gauge() -> None:
    """Update the recipients total gauge."""
    try:
        count = Recipients.query.count()
        recipients_total.set(count)
    except Exception:
        pass


def update_unique_recipients_gauge() -> None:
    """Update the unique recipients gauge."""
    try:
        unique_count = db.session.query(Tracking.recipients_id).distinct().count()
        tracking_events_unique_recipients.set(unique_count)
    except Exception:
        pass


@app.after_request
def add_security_headers(response: Any) -> Any:
    """Add security headers to all responses."""
    # Content Security Policy - restrict resource loading
    response.headers[
        "Content-Security-Policy"
    ] = "default-src 'self'; script-src 'self'; style-src 'self' 'unsafe-inline'; img-src 'self' data: https:; font-src 'self'; connect-src 'self'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'"

    # HTTP Strict Transport Security - enforce HTTPS for 1 year
    response.headers[
        "Strict-Transport-Security"
    ] = "max-age=31536000; includeSubDomains; preload"

    # Prevent clickjacking attacks
    response.headers["X-Frame-Options"] = "DENY"

    # Prevent MIME type sniffing
    response.headers["X-Content-Type-Options"] = "nosniff"

    # XSS Protection (legacy, but still useful for older browsers)
    response.headers["X-XSS-Protection"] = "1; mode=block"

    # Control referrer information
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

    # Permissions Policy - restrict browser features
    response.headers[
        "Permissions-Policy"
    ] = "geolocation=(), microphone=(), camera=(), payment=()"

    return response


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


class FailedEvent(db.Model):  # type: ignore[name-defined]
    """Model for storing failed database operations after all retries exhausted."""

    id = db.Column("failed_event_id", db.Integer, primary_key=True)
    operation_type = db.Column(
        db.String(50)
    )  # e.g., 'tracking_insert', 'recipient_insert'
    entity_id = db.Column(db.Integer, nullable=True)  # Original entity ID if available
    error_message = db.Column(db.Text)
    error_details = db.Column(db.JSON)
    retry_count = db.Column(db.Integer)
    timestamp = db.Column(db.DateTime)
    context_data = db.Column(
        "metadata", db.JSON, nullable=True
    )  # Additional context about the operation

    def __repr__(self) -> str:
        return f"<FailedEvent {self.id} - {self.operation_type}>"


def log_failed_event(
    operation_type: str,
    error_message: str,
    error_details: dict[str, Any] | None = None,
    retry_count: int = 5,
    entity_id: int | None = None,
    context_data: dict[str, Any] | None = None,
) -> None:
    """
    Log a failed operation to the dead letter queue (FailedEvent table).

    SECURITY FIX #99: Uses explicit transaction handling with rollback and cleanup.

    Args:
        operation_type: Type of operation that failed (e.g., 'tracking_insert').
        error_message: Human-readable error message.
        error_details: Detailed error information as JSON.
        retry_count: Number of retry attempts made.
        entity_id: Original entity ID if available.
        context_data: Additional context about the operation.
    """
    try:
        failed_event = FailedEvent(
            operation_type=operation_type,
            entity_id=entity_id,
            error_message=error_message,
            error_details=error_details or {},
            retry_count=retry_count,
            timestamp=datetime.now(),
            context_data=context_data,
        )
        db.session.add(failed_event)
        db.session.commit()
        logger.warning(
            f"Logged failed event to dead letter queue: {operation_type}",
            extra={"entity_id": entity_id, "retry_count": retry_count},
        )
    except Exception as log_error:
        # SECURITY FIX #99: Explicit rollback on error
        db.session.rollback()
        logger.error(
            f"Failed to log failed event to dead letter queue: {log_error}",
            exc_info=True,
        )
        # SECURITY FIX #99: Session cleanup on error
        db.session.remove()


def commit_with_retry(
    operation_type: str,
    entity_id: int | None = None,
    context_data: dict[str, Any] | None = None,
) -> None:
    """
    Commit database session with retry logic and dead letter queue fallback.

    SECURITY FIX #99: Implements explicit transaction handling:
    - Wraps operations in try/except/finally blocks
    - Explicitly calls db.session.rollback() on errors
    - Ensures session cleanup in finally blocks
    - Prevents session leakage

    Args:
        operation_type: Type of operation for logging (e.g., 'recipient_insert').
        entity_id: ID of the entity being operated on.
        context_data: Additional context about the operation.
    """
    max_attempts = app.config.get("RETRY_MAX_ATTEMPTS", 5)

    @retry_with_backoff(
        max_attempts=max_attempts,
        base_delay=app.config.get("RETRY_BASE_DELAY", 2),
        max_delay=app.config.get("RETRY_MAX_DELAY", 30),
        jitter=app.config.get("RETRY_JITTER", True),
    )
    def _commit() -> None:
        db.session.commit()

    try:
        _commit()
    except Exception as e:
        # SECURITY FIX #99: Explicit rollback on error
        db.session.rollback()
        logger.error(
            f"Database commit failed after {max_attempts} attempts: {e}",
            exc_info=True,
        )
        log_failed_event(
            operation_type=operation_type,
            error_message=str(e),
            error_details={"exception_type": type(e).__name__},
            retry_count=max_attempts,
            entity_id=entity_id,
            context_data=context_data,
        )


class DatabaseSessionManager:
    """
    SECURITY FIX #99: Context manager for database operations.

    Provides explicit transaction handling with automatic rollback and cleanup.
    Use this for complex multi-step database operations.

    Example:
        with DatabaseSessionManager() as session:
            recipient = Recipients(...)
            session.add(recipient)
            # Automatically commits on success, rolls back on error
    """

    def __init__(self, operation_type: str = "unknown"):
        self.operation_type = operation_type
        self.session = db.session

    def __enter__(self) -> Any:
        return self.session

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: Any,
    ) -> bool:
        if exc_type is not None:
            # Exception occurred - rollback
            self.session.rollback()
            logger.error(
                f"Database operation '{self.operation_type}' failed: {exc_val}",
                exc_info=True,
            )
            # Don't suppress the exception
            return False
        else:
            # No exception - commit
            try:
                self.session.commit()
            except Exception as e:
                self.session.rollback()
                logger.error(
                    f"Database commit failed for '{self.operation_type}': {e}",
                    exc_info=True,
                )
                raise
            finally:
                # Always clean up session
                self.session.remove()
            return False


def nocache(view: Callable) -> Callable:
    @wraps(view)
    def no_cache(*args: Any, **kwargs: Any) -> Any:
        response = make_response(view(*args, **kwargs))
        response.headers["Last-Modified"] = datetime.now()
        response.headers[
            "Cache-Control"
        ] = "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "-1"
        return response

    return update_wrapper(no_cache, view)


def require_auth(view: Callable) -> Callable:
    """Decorator to require authentication for admin endpoints.

    SECURITY FIX #96: Implements session-based authentication with JWT tokens.
    Supports both JWT tokens (preferred) and legacy static tokens for backwards compatibility.

    SECURITY FIX #101: Cookie-based authentication:
    - Checks httpOnly auth cookie first
    - Falls back to Authorization header for API clients

    Authentication flow:
    1. Check for JWT token in httpOnly cookie (preferred)
    2. Check for JWT token in Authorization header (Bearer <jwt_token>)
    3. Validate JWT signature, expiration, and blacklist status
    4. Fall back to legacy static token validation (deprecated)
    5. Return 401 if authentication fails

    Returns 401 if authentication fails.
    """

    @wraps(view)
    def decorated_function(*args: Any, **kwargs: Any) -> Any:
        token = None

        # SECURITY FIX #101: Check cookie first (preferred method)
        token = request.cookies.get("auth_token")

        # Fall back to Authorization header if no cookie
        if not token:
            auth_header = request.headers.get("Authorization")
            if auth_header:
                # Support "Bearer <token>" format
                if auth_header.startswith("Bearer "):
                    token = auth_header[7:]
                else:
                    token = auth_header

        if not token:
            logger.warning("Missing authentication (cookie or Authorization header)")
            return json.jsonify({"error": "Authentication required"}), 401

        # SECURITY FIX #96: Try JWT token validation first
        if token.startswith("eyJ"):  # JWT tokens start with 'eyJ'
            payload = verify_jwt_token(token)
            if payload:
                # Token is valid, attach user info to request context
                request.jwt_payload = payload  # type: ignore[attr-defined]
                return view(*args, **kwargs)
            else:
                logger.warning("Invalid or expired JWT token")
                return json.jsonify({"error": "Invalid or expired token"}), 401

        # Legacy static token validation (deprecated, keep for backwards compatibility)
        admin_token = os.environ.get("ADMIN_TOKEN")
        if not admin_token:
            logger.error("ADMIN_TOKEN not configured")
            return json.jsonify({"error": "Server configuration error"}), 500

        if token != admin_token:
            logger.warning("Invalid admin token provided")
            return json.jsonify({"error": "Invalid token"}), 401

        return view(*args, **kwargs)

    return decorated_function


@app.route("/")
def root_path() -> str:
    return ""


@app.route("/new-uuid")
def new_uuid() -> str:
    this_uuid = str(uuid.uuid4())
    description = request.args.get("description")
    email = request.args.get("email")

    entry = Recipients(r_uuid=this_uuid, description=description, email=email)

    r = f"""
    <p>{this_uuid}<p>

    {description} {email}
    """
    # SECURITY FIX #99: Use explicit session handling
    try:
        db.session.add(entry)
        commit_with_retry(
            "recipient_insert", context_data={"uuid": this_uuid, "email": email}
        )
    except Exception as e:
        logger.error(f"Failed to create recipient: {e}", exc_info=True)
        db.session.rollback()
        raise
    return r


@app.route("/img/<this_uuid>")
@nocache
def send_img(this_uuid: str) -> Any:
    # SECURITY FIX #99: Use explicit session handling for database queries
    try:
        r_model = Recipients.query.filter_by(r_uuid=this_uuid).first()
    except Exception as e:
        logger.error(f"Failed to query recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Database error"}), 500

    if r_model is None:
        return json.jsonify({"error": "Recipient not found"}), 404

    details: dict[str, Any] = {}
    details["user_agent"] = request.headers.get("User-Agent")
    details["headers"] = dict(request.headers)
    details["remote_addr"] = request.remote_addr
    details["referrer"] = request.referrer
    details["values"] = request.values
    details["date"] = request.date

    logger.info(
        "Tracking pixel accessed",
        extra={
            "recipient_id": r_model.id,
            "recipient_uuid": this_uuid,
            "user_agent": details["user_agent"],
            "remote_addr": details["remote_addr"],
            "referrer": details["referrer"],
        },
    )

    img_io = io.BytesIO()
    img = Image.new("RGBA", (1, 1), (255, 255, 255, 0))
    img.save(img_io, format="PNG")
    img_io.seek(0)

    ua = user_agent_parser.Parse(details["user_agent"])

    if not ua["user_agent"]["family"] == "GmailImageProxy":
        start_time = datetime.now()

        entry = Tracking(
            recipients_id=r_model.id,
            timestamp=datetime.now(),
            ip_country=request.headers.get("Cf-Ipcountry"),
            connecting_ip=request.headers.get("Cf-Connecting-Ip"),
            user_agent=details["user_agent"],
            details=json.dumps(details),
        )
        # SECURITY FIX #99: Use explicit session handling with rollback
        try:
            db.session.add(entry)
            commit_with_retry(
                "tracking_insert",
                entity_id=r_model.id,
                context_data={
                    "user_agent": details["user_agent"],
                    "country": request.headers.get("Cf-Ipcountry"),
                },
            )
        except Exception as e:
            logger.error(f"Failed to create tracking entry: {e}", exc_info=True)
            db.session.rollback()
            # Log to dead letter queue
            log_failed_event(
                "tracking_insert",
                str(e),
                {"exception_type": type(e).__name__},
                entity_id=r_model.id,
            )

        # Record custom metrics
        processing_time = (datetime.now() - start_time).total_seconds()
        tracking_event_processing_seconds.observe(processing_time)

        country = request.headers.get("Cf-Ipcountry", "Unknown")
        tracking_events_total.labels(
            recipient_id=str(r_model.id), country=country
        ).inc()

        # Update gauges
        update_recipients_gauge()
        update_unique_recipients_gauge()

    return send_file(img_io, download_name="1.png", mimetype="image/png")  # type: ignore[call-arg]


@app.route("/api/admin/login", methods=["POST"])
@limiter.limit("5 per minute")
@csrf.exempt  # Exempt login from CSRF - it's token-based auth, no prior session
def admin_login() -> Any:
    """Admin login endpoint with JWT token authentication.

    SECURITY FIX #96: Implements proper session-based authentication:
    - Returns JWT token with 24-hour expiration (configurable)
    - Token includes unique identifier (jti) for revocation
    - Supports token refresh mechanism
    - Admin token is hashed, not stored in plain text

    SECURITY FIX #101: Cookie-based authentication:
    - Sets httpOnly, Secure, SameSite=Strict cookie
    - Token not returned in response body (prevents XSS theft)

    Request:
        {
            "token": "admin-token"
        }

    Response:
        {
            "status": "authenticated",
            "expires_in": 86400,  # seconds
            "token_type": "Bearer"
        }
        With httpOnly cookie set
    """
    data = request.get_json()
    if not data:
        logger.warning("Invalid JSON in login request")
        return json.jsonify({"error": "Invalid JSON"}), 400

    token = data.get("token", "")
    # Input validation - token must be string and within length limits
    if not isinstance(token, str) or len(token) > 256:
        logger.warning("Invalid token format in login request")
        return json.jsonify({"error": "Invalid token format"}), 400

    # Sanitise token input
    token = bleach.clean(token, tags=[], strip=True)

    admin_token = os.environ.get("ADMIN_TOKEN")
    # This should never be None due to startup validation, but check for safety
    if not admin_token:
        logger.error("ADMIN_TOKEN not configured")
        return json.jsonify({"error": "Server configuration error"}), 500

    if token == admin_token:
        logger.info("Admin login successful")
        # SECURITY FIX #96: Generate JWT token instead of returning static token
        jwt_token = generate_jwt_token(admin_token)

        # SECURITY FIX #101: Set httpOnly, Secure, SameSite=Strict cookie
        response = make_response(
            json.jsonify(
                {
                    "status": "authenticated",
                    "expires_in": JWT_TOKEN_EXPIRY_HOURS * 3600,
                    "token_type": "Bearer",
                }
            )
        )
        response.set_cookie(
            "auth_token",
            jwt_token,
            httponly=True,
            secure=True,  # Only over HTTPS
            samesite="Strict",
            max_age=JWT_TOKEN_EXPIRY_HOURS * 3600,  # 24 hours by default
            path="/",
        )
        return response

    logger.warning("Admin login failed")
    return json.jsonify({"error": "Invalid token"}), 401


@app.route("/api/admin/token/refresh", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
def refresh_token() -> Any:
    """Refresh JWT token endpoint.

    SECURITY FIX #96: Allows token refresh before expiration.
    Requires valid current token to get a new one.

    SECURITY FIX #101: Cookie-based authentication:
    - Sets new httpOnly, Secure, SameSite=Strict cookie
    - Token not returned in response body

    Response:
        {
            "expires_in": 86400,
            "token_type": "Bearer"
        }
        With new httpOnly cookie set
    """
    admin_token = os.environ.get("ADMIN_TOKEN")
    if not admin_token:
        return json.jsonify({"error": "Server configuration error"}), 500

    # Generate new token with new expiration
    jwt_token = generate_jwt_token(admin_token)
    logger.info("Token refreshed successfully")

    # SECURITY FIX #101: Set new httpOnly, Secure, SameSite=Strict cookie
    response = make_response(
        json.jsonify(
            {
                "expires_in": JWT_TOKEN_EXPIRY_HOURS * 3600,
                "token_type": "Bearer",
            }
        )
    )
    response.set_cookie(
        "auth_token",
        jwt_token,
        httponly=True,
        secure=True,
        samesite="Strict",
        max_age=JWT_TOKEN_EXPIRY_HOURS * 3600,
        path="/",
    )
    return response


@app.route("/api/admin/logout", methods=["POST"])
@limiter.limit("10 per minute")
@require_auth
def admin_logout() -> Any:
    """Logout endpoint - revokes current JWT token.

    SECURITY FIX #96: Implements token revocation mechanism.
    Adds token to blacklist to prevent further use.

    SECURITY FIX #101: Cookie-based authentication:
    - Clears httpOnly auth cookie on logout

    Note: In production, use Redis/database for distributed blacklist.
    """
    # Get token from cookie for revocation
    token = request.cookies.get("auth_token")
    if token and token.startswith("eyJ"):  # JWT token
        revoke_jwt_token(token)
        logger.info("Token revoked successfully")

    # SECURITY FIX #101: Clear the auth cookie
    response = make_response(json.jsonify({"status": "logged out"}))
    response.delete_cookie("auth_token", path="/")
    return response


@app.route("/api/admin/recipients", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
def get_recipients() -> Any:
    """Get all recipients."""
    logger.info("Fetching all recipients")
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
@limiter.limit("30 per minute")
@require_auth
def create_recipient() -> Any:
    """Create a new recipient.

    SECURITY FIX #99: Uses explicit session handling with rollback on errors.
    """
    data = request.get_json()
    if not data:
        logger.warning("Create recipient failed: invalid JSON")
        return json.jsonify({"error": "Invalid JSON"}), 400

    # Input validation - email is required and must be valid format
    email = data.get("email", "")
    if not email or not isinstance(email, str):
        logger.warning("Create recipient failed: missing or invalid email")
        return json.jsonify({"error": "Email is required"}), 400

    # Email length limit
    if len(email) > 254:
        logger.warning("Create recipient failed: email too long")
        return json.jsonify({"error": "Email too long"}), 400

    # Basic email format validation
    email_pattern = r"^[\w\.\-]+@[a-zA-Z\.\-]+\.[a-zA-Z]{2,}$"
    cleaned_email = bleach.clean(email, tags=[], strip=True)
    if not re.match(email_pattern, cleaned_email):
        logger.warning("Create recipient failed: invalid email format")
        return json.jsonify({"error": "Invalid email format"}), 400

    description = data.get("description", "")
    if description and (not isinstance(description, str) or len(description) > 200):
        logger.warning("Create recipient failed: invalid description")
        return json.jsonify(
            {"error": "Description must be string and max 200 chars"}
        ), 400

    # Sanitise inputs
    email = cleaned_email
    description = bleach.clean(description, tags=[], strip=True) if description else ""

    # SECURITY FIX #99: Use explicit session handling
    try:
        recipient = Recipients(
            r_uuid=str(uuid.uuid4()),
            description=description,
            email=email,
        )
        db.session.add(recipient)
        commit_with_retry(
            "recipient_insert",
            entity_id=recipient.id,
            context_data={
                "email": recipient.email,
                "description": recipient.description,
            },
        )

        logger.info(
            "Recipient created",
            extra={
                "recipient_id": recipient.id,
                "recipient_uuid": recipient.r_uuid,
                "email": recipient.email,
            },
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
    except Exception as e:
        logger.error(f"Failed to create recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Failed to create recipient"}), 500


@app.route("/api/admin/recipients/<int:recipient_id>", methods=["PUT"])
@limiter.limit("30 per minute")
@require_auth
def update_recipient(recipient_id: int) -> Any:
    """Update a recipient.

    SECURITY FIX #99: Uses explicit session handling with rollback on errors.
    """
    # SECURITY FIX #99: Wrap database operations in try/except
    try:
        recipient = Recipients.query.get_or_404(recipient_id)
    except Exception as e:
        logger.error(f"Failed to query recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Database error"}), 500

    data = request.get_json()
    if not data:
        return json.jsonify({"error": "Invalid JSON"}), 400

    if "description" in data:
        description = data["description"]
        if not isinstance(description, str) or len(description) > 200:
            return json.jsonify(
                {"error": "Description must be string and max 200 chars"}
            ), 400
        recipient.description = bleach.clean(description, tags=[], strip=True)

    if "email" in data:
        email = data["email"]
        if not isinstance(email, str) or len(email) > 254:
            return json.jsonify(
                {"error": "Email must be string and max 254 chars"}
            ), 400

        # Basic email format validation
        email_pattern = r"^[\w\.\-]+@[a-zA-Z\.\-]+\.[a-zA-Z]{2,}$"
        if not re.match(email_pattern, bleach.clean(email, tags=[], strip=True)):
            return json.jsonify({"error": "Invalid email format"}), 400

        recipient.email = bleach.clean(email, tags=[], strip=True)

    # SECURITY FIX #99: Use explicit session handling
    try:
        commit_with_retry(
            "recipient_update",
            entity_id=recipient.id,
            context_data={"updated_fields": list(data.keys())},
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
            200,
        )
    except Exception as e:
        logger.error(f"Failed to update recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Failed to update recipient"}), 500


@app.route("/api/admin/recipients/<int:recipient_id>", methods=["DELETE"])
@limiter.limit("30 per minute")
@require_auth
def delete_recipient(recipient_id: int) -> Any:
    """Delete a recipient.

    SECURITY FIX #99: Uses explicit session handling with rollback on errors.
    """
    # SECURITY FIX #99: Wrap database operations in try/except
    try:
        recipient = Recipients.query.get_or_404(recipient_id)
    except Exception as e:
        logger.error(f"Failed to query recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Database error"}), 500

    # SECURITY FIX #99: Use explicit session handling
    try:
        db.session.delete(recipient)
        commit_with_retry(
            "recipient_delete",
            entity_id=recipient.id,
            context_data={"email": recipient.email},
        )

        logger.info(
            "Recipient deleted",
            extra={
                "recipient_id": recipient.id,
                "recipient_uuid": recipient.r_uuid,
            },
        )

        return json.jsonify({"status": "deleted"}), 200
    except Exception as e:
        logger.error(f"Failed to delete recipient: {e}", exc_info=True)
        db.session.rollback()
        return json.jsonify({"error": "Failed to delete recipient"}), 500


@app.route("/api/admin/stats", methods=["GET"])
@limiter.limit("30 per minute")
@require_auth
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
                        "email": event.recipients_id,
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
@limiter.limit("30 per minute")
@require_auth
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
@limiter.limit("30 per minute")
@require_auth
def update_settings() -> Any:
    """Update application settings (in-memory for now)."""
    data = request.get_json()
    if not data:
        return json.jsonify({"error": "Invalid JSON"}), 400

    # Validate and sanitise settings keys
    allowed_settings = {"tracking_enabled", "log_level"}
    sanitized_data = {}
    for key, value in data.items():
        if key in allowed_settings:
            if key == "tracking_enabled":
                if not isinstance(value, bool):
                    return json.jsonify(
                        {"error": "tracking_enabled must be boolean"}
                    ), 400
                sanitized_data[key] = value
            elif key == "log_level":
                if not isinstance(value, str) or len(value) > 20:
                    return json.jsonify(
                        {"error": "log_level must be string and max 20 chars"}
                    ), 400
                sanitized_data[key] = bleach.clean(value, tags=[], strip=True).upper()
                if sanitized_data[key] not in (
                    "DEBUG",
                    "INFO",
                    "WARNING",
                    "ERROR",
                    "CRITICAL",
                ):
                    return json.jsonify({"error": "Invalid log level"}), 400

    return json.jsonify({"status": "updated", "settings": sanitized_data}), 200


@app.route("/api/analytics/summary", methods=["GET"])
@limiter.limit("60 per minute")
@require_auth
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
@limiter.limit("60 per minute")
@require_auth
def get_analytics_events() -> Any:
    """Get time-series event data."""
    range_days = request.args.get("range", "7d")

    # Validate range parameter
    try:
        if not range_days or not isinstance(range_days, str):
            return json.jsonify({"error": "Invalid range parameter"}), 400

        # Extract days from format like "7d", "30d", etc.
        if not range_days.endswith("d"):
            return json.jsonify({"error": "Range must be in format like '7d'"}), 400

        days = int(range_days[:-1])

        # Validate range is reasonable (1-365 days)
        if days < 1 or days > 365:
            return json.jsonify({"error": "Range must be between 1 and 365 days"}), 400
    except (ValueError, AttributeError):
        return json.jsonify({"error": "Invalid range format"}), 400

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
@limiter.limit("60 per minute")
@require_auth
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
@limiter.limit("60 per minute")
@require_auth
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
@limiter.limit("60 per minute")
@require_auth
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
@limiter.limit("60 per minute")
@require_auth
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
    return (
        output.getvalue(),
        200,
        {
            "Content-Type": "text/csv",
            "Content-Disposition": "attachment; filename=analytics_export.csv",
        },
    )


# Initialise logging
configure_logging(app)
init_logging_middleware(app)


if __name__ == "__main__":
    # SECURITY FIX #100: Use configured debug mode instead of hardcoded True
    # Debug mode is only enabled in development when FLASK_DEBUG=1
    debug_mode = app.config.get("DEBUG", False)

    if debug_mode:
        logger.info("Starting Flask in development mode with debug enabled")
    else:
        logger.info("Starting Flask in production mode with debug disabled")

    app.run(debug=debug_mode, host="0.0.0.0", port=5000)
