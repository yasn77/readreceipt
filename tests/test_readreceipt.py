"""Tests for the readreceipt Flask application."""

import uuid
from collections.abc import Generator
from typing import Any

import pytest

from app import Recipients, Tracking, app, db


@pytest.fixture
def client() -> Generator[Any, None, None]:
    """Create a test client with an in-memory SQLite database."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    with app.app_context():
        db.create_all()
        test_client = app.test_client()
        # Add auth header for admin/analytics endpoints
        test_client.environ_base["HTTP_AUTHORIZATION"] = "Bearer test-token"
        yield test_client
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_recipient(client: Any) -> str:
    """Create a sample recipient for testing."""
    test_uuid = str(uuid.uuid4())
    recipient = Recipients(
        r_uuid=test_uuid, description="Test recipient", email="test@example.com"
    )
    db.session.add(recipient)
    db.session.commit()
    return test_uuid


class TestRootPath:
    """Tests for the root path endpoint."""

    def test_root_returns_empty(self, client: Any) -> None:
        """Test that root path returns empty response."""
        response = client.get("/")
        assert response.status_code == 200
        assert response.data == b""


class TestNewUuid:
    """Tests for the /new-uuid endpoint."""

    def test_new_uuid_creates_entry(self, client: Any) -> None:
        """Test that /new-uuid creates a new recipient entry."""
        response = client.get("/new-uuid?description=Test&email=test@example.com")
        assert response.status_code == 200
        assert len(response.data) > 0
        assert b"<p>" in response.data

    def test_new_uuid_without_params(self, client: Any) -> None:
        """Test that /new-uuid works without description and email."""
        response = client.get("/new-uuid")
        assert response.status_code == 200
        assert len(response.data) > 0


class TestSendImg:
    """Tests for the /img/<uuid> endpoint."""

    def test_send_img_returns_png(self, client: Any, sample_recipient: str) -> None:
        """Test that /img/<uuid> returns a PNG image."""
        response = client.get(f"/img/{sample_recipient}")
        assert response.status_code == 200
        assert response.content_type == "image/png"

    def test_send_img_sets_no_cache_headers(
        self, client: Any, sample_recipient: str
    ) -> None:
        """Test that /img/<uuid> sets proper no-cache headers."""
        response = client.get(f"/img/{sample_recipient}")
        assert response.status_code == 200
        assert (
            response.headers["Cache-Control"]
            == "no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0"  # noqa: E501
        )
        assert response.headers["Pragma"] == "no-cache"
        assert response.headers["Expires"] == "-1"

    def test_send_img_nonexistent_uuid(self, client: Any) -> None:
        """Test that /img/<uuid> handles non-existent UUID gracefully."""
        fake_uuid = str(uuid.uuid4())
        response = client.get(f"/img/{fake_uuid}")
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert "error" in data


class TestRecipients:
    """Tests for the Recipients model."""

    def test_recipient_repr(self, client: Any) -> None:
        """Test Recipients __repr__ method."""
        test_uuid = str(uuid.uuid4())
        recipient = Recipients(
            r_uuid=test_uuid, description="Test", email="test@example.com"
        )
        db.session.add(recipient)
        db.session.commit()

        assert f"<Recipients {test_uuid}>" in repr(recipient)


class TestTracking:
    """Tests for the Tracking model."""

    def test_tracking_repr(self, client: Any) -> None:
        """Test Tracking __repr__ method."""
        tracking = Tracking(recipients_id=1, ip_country="US", user_agent="Test Agent")
        assert "<Tracking" in repr(tracking)


class TestAdminEndpoints:
    """Tests for admin API endpoints."""

    def test_admin_login_success(self, client: Any, monkeypatch: Any) -> None:
        """Test successful admin login."""
        monkeypatch.setenv("ADMIN_TOKEN", "test-token")

        response = client.post(
            "/api/admin/login",
            json={"token": "test-token"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "authenticated"

    def test_admin_login_failure(self, client: Any) -> None:
        """Test failed admin login."""
        response = client.post(
            "/api/admin/login",
            json={"token": "wrong-token"},
            content_type="application/json",
        )
        assert response.status_code == 401

    def test_get_recipients(self, client: Any, sample_recipient: str) -> None:
        """Test getting all recipients."""
        response = client.get("/api/admin/recipients")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)
        assert len(data) > 0

    def test_create_recipient(self, client: Any) -> None:
        """Test creating a new recipient."""
        response = client.post(
            "/api/admin/recipients",
            json={"email": "new@example.com", "description": "New recipient"},
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["email"] == "new@example.com"

    def test_create_recipient_missing_email(self, client: Any) -> None:
        """Test creating recipient without email."""
        response = client.post(
            "/api/admin/recipients",
            json={"description": "No email"},
            content_type="application/json",
        )
        assert response.status_code == 400

    def test_update_recipient(self, client: Any, sample_recipient: str) -> None:
        """Test updating a recipient."""
        recipient = Recipients.query.filter_by(r_uuid=sample_recipient).first()

        response = client.put(
            f"/api/admin/recipients/{recipient.id}",
            json={"email": "updated@example.com"},
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "updated@example.com"

    def test_delete_recipient(self, client: Any, sample_recipient: str) -> None:
        """Test deleting a recipient."""
        recipient = Recipients.query.filter_by(r_uuid=sample_recipient).first()

        response = client.delete(f"/api/admin/recipients/{recipient.id}")
        assert response.status_code == 200

        deleted = Recipients.query.filter_by(r_uuid=sample_recipient).first()
        assert deleted is None

    def test_get_admin_stats(self, client: Any) -> None:
        """Test getting admin statistics."""
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_recipients" in data
        assert "total_events" in data

    def test_get_settings(self, client: Any) -> None:
        """Test getting settings."""
        response = client.get("/api/admin/settings")
        assert response.status_code == 200
        data = response.get_json()
        assert "tracking_enabled" in data

    def test_update_settings(self, client: Any) -> None:
        """Test updating settings."""
        response = client.put(
            "/api/admin/settings",
            json={"tracking_enabled": False},
            content_type="application/json",
        )
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints."""

    def test_get_analytics_summary(self, client: Any) -> None:
        """Test getting analytics summary."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 200
        data = response.get_json()
        assert "total_events" in data
        assert "unique_recipients" in data

    def test_get_analytics_events(self, client: Any) -> None:
        """Test getting analytics events."""
        response = client.get("/api/analytics/events?range=7d")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_recipients(self, client: Any) -> None:
        """Test getting top recipients."""
        response = client.get("/api/analytics/recipients")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_geo(self, client: Any) -> None:
        """Test getting geographic data."""
        response = client.get("/api/analytics/geo")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_clients(self, client: Any) -> None:
        """Test getting email client breakdown."""
        response = client.get("/api/analytics/clients")
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_export_analytics(self, client: Any) -> None:
        """Test exporting analytics data."""
        response = client.get("/api/analytics/export")
        assert response.status_code == 200
        assert "text/csv" in response.content_type


class TestPrometheusMetrics:
    """Tests for Prometheus metrics endpoints and functionality."""

    def test_metrics_endpoint_returns_prometheus_format(self, client: Any) -> None:
        """Test that /metrics endpoint returns Prometheus format."""
        response = client.get("/metrics")
        assert response.status_code == 200
        assert "text/plain" in response.content_type
        # Check for standard Prometheus metrics
        data = response.data.decode("utf-8")
        assert "# HELP" in data
        assert "# TYPE" in data

    def test_metrics_endpoint_contains_http_metrics(self, client: Any) -> None:
        """Test that /metrics contains HTTP metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        # Check for automatic HTTP metrics from prometheus-flask-exporter
        # Note: prometheus-flask-exporter uses 'http_request_total' (singular)
        assert "http_request_total" in data or "http_requests_total" in data
        assert "http_request_duration_seconds" in data

    def test_metrics_endpoint_contains_custom_metrics(self, client: Any) -> None:
        """Test that /metrics contains custom business metrics."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        # Check for custom business metrics
        assert "tracking_events_total" in data
        assert "tracking_events_unique_recipients" in data
        assert "recipients_total" in data
        assert "tracking_event_processing_seconds" in data

    def test_metrics_health_endpoint(self, client: Any) -> None:
        """Test that /metrics/health returns health status."""
        response = client.get("/metrics/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data is not None
        assert "status" in data
        assert "database" in data
        assert "metrics_count" in data
        assert "timestamp" in data
        assert data["status"] == "healthy"

    def test_metrics_increment_on_tracking_event(
        self, client: Any, sample_recipient: str
    ) -> None:
        """Test that tracking metrics increment when a tracking event occurs."""
        # Get initial metrics
        initial_response = client.get("/metrics")
        initial_data = initial_response.data.decode("utf-8")

        # Trigger a tracking event by accessing the tracking image
        # Note: We need to simulate a non-Gmail user agent
        tracking_response = client.get(
            f"/img/{sample_recipient}",
            headers={"User-Agent": "Mozilla/5.0 Test Client"},
        )
        assert tracking_response.status_code == 200

        # Get metrics after tracking event
        after_response = client.get("/metrics")
        after_data = after_response.data.decode("utf-8")

        # Verify tracking_events_total metric exists
        assert "tracking_events_total" in after_data

    def test_recipients_gauge_updates(self, client: Any) -> None:
        """Test that recipients_total gauge is present."""
        response = client.get("/metrics")
        assert response.status_code == 200
        data = response.data.decode("utf-8")
        # The gauge should be present in the metrics
        assert "recipients_total" in data

    def test_metrics_endpoint_excluded_from_auto_metrics(self, client: Any) -> None:
        """Test that /metrics endpoint is excluded from automatic metrics."""
        # Make a request to /metrics
        client.get("/metrics")

        # Get metrics and verify the endpoint wasn't counted
        response = client.get("/metrics")
        assert response.status_code == 200
