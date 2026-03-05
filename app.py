from __future__ import annotations

import io
import logging
import os
import re
import uuid
from collections.abc import Callable
from datetime import datetime
from functools import update_wrapper, wraps
from typing import Any

import bleach
from flask import Flask, json, make_response, request, send_file
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy.query import Query
from PIL import Image
from prometheus_client import (
    Counter,
    Gauge,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST,
)
from prometheus_flask_exporter import PrometheusMetrics
from sqlalchemy_utils import CountryType, IPAddressType
from ua_parser import user_agent_parser

from utils.logging import configure_logging, init_logging_middleware
from utils.retry import retry_with_backoff

app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", os.urandom(32).hex())

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

# Rate limiting configuration
limiter = Limiter(
    key_func=get_remote_address,
    app=app,
    default_limits=["120 per minute"],
    storage_uri="memory://",
)

db = SQLAlchemy(app)
migrate = Migrate(app, db)
logger = logging.getLogger(__name__)

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
        logger.error(
            f"Failed to log failed event to dead letter queue: {log_error}",
            exc_info=True,
        )


def commit_with_retry(
    operation_type: str,
    entity_id: int | None = None,
    context_data: dict[str, Any] | None = None,
) -> None:
    """
    Commit database session with retry logic and dead letter queue fallback.

    Args:
        operation_type: Type of operation for logging (e.g., 'recipient_insert').
        entity_id: ID of the entity being operated on.
        metadata: Additional context about the operation.
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
    db.session.add(entry)
    commit_with_retry(
        "recipient_insert", context_data={"uuid": this_uuid, "email": email}
    )
    return r


@app.route("/img/<this_uuid>")
@nocache
def send_img(this_uuid: str) -> Any:
    r_model = Recipients.query.filter_by(r_uuid=this_uuid).first()

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
        db.session.add(entry)
        commit_with_retry(
            "tracking_insert",
            entity_id=r_model.id,
            context_data={
                "user_agent": details["user_agent"],
                "country": request.headers.get("Cf-Ipcountry"),
            },
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
def admin_login() -> Any:
    """Admin login endpoint with token authentication."""
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

    admin_token = os.environ.get("ADMIN_TOKEN", "admin")

    if token == admin_token:
        logger.info("Admin login successful")
        return json.jsonify({"status": "authenticated"}), 200
    logger.warning("Admin login failed")
    return json.jsonify({"error": "Invalid token"}), 401


@app.route("/api/admin/recipients", methods=["GET"])
@limiter.limit("30 per minute")
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
def create_recipient() -> Any:
    """Create a new recipient."""
    data = request.get_json()

    if not data.get("email"):
        logger.warning("Create recipient failed: missing email")
        return json.jsonify({"error": "Email is required"}), 400

    recipient = Recipients(
        r_uuid=str(uuid.uuid4()),
        description=data.get("description", ""),
        email=data["email"],
    )
    db.session.add(recipient)
    commit_with_retry(
        "recipient_insert",
        entity_id=recipient.id,
        context_data={"email": recipient.email, "description": recipient.description},
    )

    logger.info(
        "Recipient created",
        recipient_id=recipient.id,
        recipient_uuid=recipient.r_uuid,
        email=recipient.email,
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
@limiter.limit("30 per minute")
def update_recipient(recipient_id: int) -> Any:
    """Update a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
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


@app.route("/api/admin/recipients/<int:recipient_id>", methods=["DELETE"])
@limiter.limit("30 per minute")
def delete_recipient(recipient_id: int) -> Any:
    """Delete a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
    db.session.delete(recipient)
    commit_with_retry(
        "recipient_delete",
        entity_id=recipient.id,
        context_data={"email": recipient.email},
    )

    logger.info(
        "Recipient deleted",
        recipient_id=recipient.id,
        recipient_uuid=recipient.r_uuid,
    )

    return json.jsonify({"status": "deleted"}), 200


@app.route("/api/admin/stats", methods=["GET"])
@limiter.limit("30 per minute")
def get_admin_stats() -> Any:
    """Get dashboard statistics."""
    total_recipients = Recipients.query.count()
    total_events = Tracking.query.count()

    from datetime import datetime, timedelta

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
                        "email": Tracking.recipients_id,
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
def get_analytics_summary() -> Any:
    """Get analytics summary."""
    total_events = Tracking.query.count()
    unique_recipients = Tracking.query.distinct(Tracking.recipients_id).count()

    from datetime import datetime, timedelta

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
def get_analytics_events() -> Any:
    """Get time-series event data."""
    from datetime import datetime, timedelta

    range_days = request.args.get("range", "7d")
    days = int(range_days.replace("d", ""))
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
def export_analytics() -> Any:
    """Export analytics data as CSV."""
    import csv
    from io import StringIO

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
    app.run(debug=True, host="0.0.0.0", port=5000)
