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
        yield app.test_client()
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


def auth_headers() -> dict[str, str]:
    """Return authorization headers for admin endpoints."""
    return {"Authorization": "Bearer admin"}


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
        """Test that /img/<uuid> sets no-cache headers."""
        response = client.get(f"/img/{sample_recipient}")
        assert "no-store" in response.headers.get("Cache-Control", "")
        assert response.headers.get("Pragma") == "no-cache"
        assert response.headers.get("Expires") == "-1"

    def test_send_img_nonexistent_uuid(self, client: Any) -> None:
        """Test that /img/<uuid> returns 404 for nonexistent UUID."""
        response = client.get("/img/nonexistent-uuid")
        assert response.status_code == 404


class TestRecipients:
    """Tests for Recipients model."""

    def test_recipient_repr(self, client: Any) -> None:
        """Test Recipients __repr__ method."""
        with app.app_context():
            recipient = Recipients(
                r_uuid="test-uuid", description="Test", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()
            assert "test-uuid" in repr(recipient)


class TestTracking:
    """Tests for Tracking model."""

    def test_tracking_repr(self, client: Any) -> None:
        """Test Tracking __repr__ method."""
        with app.app_context():
            tracking = Tracking(
                recipients_id=1,
                ip_country="US",
                connecting_ip="127.0.0.1",
                user_agent="Test",
                details="{}",
            )
            db.session.add(tracking)
            db.session.commit()
            assert repr(tracking).startswith("<Tracking")


class TestAdminEndpoints:
    """Tests for admin API endpoints."""

    def test_admin_login_success(self, client: Any) -> None:
        """Test successful admin login."""
        response = client.post(
            "/api/admin/login",
            json={"token": "admin"},
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
        response = client.get("/api/admin/recipients", headers=auth_headers())
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
            headers=auth_headers(),
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
            headers=auth_headers(),
        )
        assert response.status_code == 400

    def test_update_recipient(self, client: Any, sample_recipient: str) -> None:
        """Test updating a recipient."""
        recipient = Recipients.query.filter_by(r_uuid=sample_recipient).first()

        response = client.put(
            f"/api/admin/recipients/{recipient.id}",
            json={"email": "updated@example.com"},
            content_type="application/json",
            headers=auth_headers(),
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["email"] == "updated@example.com"

    def test_delete_recipient(self, client: Any, sample_recipient: str) -> None:
        """Test deleting a recipient."""
        recipient = Recipients.query.filter_by(r_uuid=sample_recipient).first()

        response = client.delete(
            f"/api/admin/recipients/{recipient.id}", headers=auth_headers()
        )
        assert response.status_code == 200

        deleted = Recipients.query.filter_by(r_uuid=sample_recipient).first()
        assert deleted is None

    def test_get_admin_stats(self, client: Any) -> None:
        """Test getting admin statistics."""
        response = client.get("/api/admin/stats", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert "total_recipients" in data
        assert "total_events" in data

    def test_get_settings(self, client: Any) -> None:
        """Test getting settings."""
        response = client.get("/api/admin/settings", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert "tracking_enabled" in data

    def test_update_settings(self, client: Any) -> None:
        """Test updating settings."""
        response = client.put(
            "/api/admin/settings",
            json={"tracking_enabled": False},
            content_type="application/json",
            headers=auth_headers(),
        )
        assert response.status_code == 200


class TestAnalyticsEndpoints:
    """Tests for analytics API endpoints."""

    def test_get_analytics_summary(self, client: Any) -> None:
        """Test getting analytics summary."""
        response = client.get("/api/analytics/summary", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert "total_events" in data
        assert "unique_recipients" in data

    def test_get_analytics_events(self, client: Any) -> None:
        """Test getting analytics events."""
        response = client.get("/api/analytics/events?range=7d", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_recipients(self, client: Any) -> None:
        """Test getting top recipients."""
        response = client.get("/api/analytics/recipients", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_geo(self, client: Any) -> None:
        """Test getting geographic data."""
        response = client.get("/api/analytics/geo", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_get_analytics_clients(self, client: Any) -> None:
        """Test getting email client breakdown."""
        response = client.get("/api/analytics/clients", headers=auth_headers())
        assert response.status_code == 200
        data = response.get_json()
        assert isinstance(data, list)

    def test_export_analytics(self, client: Any) -> None:
        """Test exporting analytics data."""
        response = client.get("/api/analytics/export", headers=auth_headers())
        assert response.status_code == 200
        assert response.content_type == "text/csv"
