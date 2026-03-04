from __future__ import annotations

import io
import os
import uuid
from collections.abc import Callable
from datetime import datetime
from functools import update_wrapper, wraps
from typing import Any

from flask import Flask, json, make_response, request, send_file
from flask_migrate import Migrate
from flask_sqlalchemy import SQLAlchemy
from PIL import Image
from sqlalchemy_utils import CountryType, IPAddressType
from ua_parser import user_agent_parser

app = Flask(__name__)
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
# app.config ['SQLALCHEMY_DATABASE_URI'] = 'postgresql://postgres:XXXXXX@XXXXX/readreceipt'
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "SQLALCHEMY_DATABASE_URI", "sqlite:///:memory:"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
migrate = Migrate(app, db)


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
    description = request.args.get("description")
    email = request.args.get("email")

    entry = Recipients(r_uuid=this_uuid, description=description, email=email)

    r = f"""
    <p>{this_uuid}<p>

    {description} {email}
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

    details: dict[str, Any] = {}
    details["user_agent"] = request.headers.get("User-Agent")
    details["headers"] = dict(request.headers)
    details["remote_addr"] = request.remote_addr
    details["referrer"] = request.referrer
    details["values"] = request.values
    details["date"] = request.date

    print(r_model.id)
    print(json.dumps(details))

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


@app.route("/api/admin/login", methods=["POST"])
def admin_login() -> Any:
    """Admin login endpoint with token authentication."""
    data = request.get_json()
    token = data.get("token")

    admin_token = os.environ.get("ADMIN_TOKEN", "admin")

    if token == admin_token:
        return json.jsonify({"status": "authenticated"}), 200
    return json.jsonify({"error": "Invalid token"}), 401


@app.route("/api/admin/recipients", methods=["GET"])
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
def create_recipient() -> Any:
    """Create a new recipient."""
    data = request.get_json()

    if not data.get("email"):
        return json.jsonify({"error": "Email is required"}), 400

    recipient = Recipients(
        r_uuid=str(uuid.uuid4()),
        description=data.get("description", ""),
        email=data["email"],
    )
    db.session.add(recipient)
    db.session.commit()

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
def update_recipient(recipient_id: int) -> Any:
    """Update a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
    data = request.get_json()

    if "description" in data:
        recipient.description = data["description"]
    if "email" in data:
        recipient.email = data["email"]

    db.session.commit()

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
def delete_recipient(recipient_id: int) -> Any:
    """Delete a recipient."""
    recipient = Recipients.query.get_or_404(recipient_id)
    db.session.delete(recipient)
    db.session.commit()

    return json.jsonify({"status": "deleted"}), 200


@app.route("/api/admin/stats", methods=["GET"])
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
def update_settings() -> Any:
    """Update application settings (in-memory for now)."""
    data = request.get_json()
    return json.jsonify({"status": "updated", "settings": data}), 200


@app.route("/api/analytics/summary", methods=["GET"])
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
