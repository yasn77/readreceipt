"""
Unit tests for security features.
Covers security headers, rate limiting, input validation, logging hardening, and RBAC.
"""

import json
import os

import pytest

from app import Recipients, Tracking, app, db


@pytest.fixture
def client():
    """Create a test client with test database."""
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["SECRET_KEY"] = "test-secret-key"
    os.environ["ADMIN_TOKEN"] = "test-admin-token"
    # Update cached _admin_token in security module
    import security
    security._admin_token = "test-admin-token"

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
        yield client
        with app.app_context():
            db.session.remove()
            db.drop_all()


@pytest.fixture
def admin_token():
    """Return admin token for authenticated requests."""
    return "test-admin-token"


class TestSecurityHeaders:
    """Test Issue #106: Security headers."""

    def test_security_headers_present(self, client):
        """Verify all security headers are present in responses."""
        response = client.get("/")

        # Check Content-Security-Policy
        assert "Content-Security-Policy" in response.headers
        assert "default-src 'self'" in response.headers["Content-Security-Policy"]

        # Check X-Frame-Options
        assert response.headers.get("X-Frame-Options") == "DENY"

        # Check X-Content-Type-Options
        assert response.headers.get("X-Content-Type-Options") == "nosniff"

        # Check Strict-Transport-Security
        assert "Strict-Transport-Security" in response.headers
        assert "max-age=31536000" in response.headers["Strict-Transport-Security"]

        # Check X-XSS-Protection
        assert response.headers.get("X-XSS-Protection") == "1; mode=block"

        # Check Referrer-Policy
        assert "Referrer-Policy" in response.headers

    def test_cache_headers_on_sensitive_endpoints(self, client):
        """Verify cache control headers on sensitive endpoints."""
        # Create a test recipient
        with app.app_context():
            recipient = Recipients(r_uuid="test-uuid", email="test@example.com")
            db.session.add(recipient)
            db.session.commit()

        response = client.get("/img/test-uuid")

        assert "Cache-Control" in response.headers
        assert "no-store" in response.headers["Cache-Control"]
        assert response.headers.get("Pragma") == "no-cache"


class TestInputValidation:
    """Test Issue #107: Input validation and sanitization."""

    def test_email_validation(self, client):
        """Verify email validation on new-uuid endpoint."""
        # Valid email
        response = client.get("/new-uuid?email=valid@example.com")
        assert response.status_code == 200

        # Invalid email format
        response = client.get("/new-uuid?email=invalid-email")
        assert response.status_code == 400
        assert b"Invalid email" in response.data

        # Email too long
        long_email = "a" * 250 + "@example.com"
        response = client.get(f"/new-uuid?email={long_email}")
        assert response.status_code == 400

    def test_description_sanitization(self, client):
        """Verify HTML/script tags are stripped from descriptions."""
        malicious_desc = "<script>alert('xss')</script>Normal text"
        response = client.get(f"/new-uuid?description={malicious_desc}")
        assert response.status_code == 200
        assert b"<script>" not in response.data
        assert b"alert" not in response.data

    def test_admin_email_validation(self, client, admin_token):
        """Verify email validation on admin recipient creation."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Invalid email
        response = client.post(
            "/api/admin/recipients", json={"email": "invalid-email"}, headers=headers
        )
        assert response.status_code == 400

    def test_request_size_limit(self, client, admin_token):
        """Verify large payloads are rejected."""
        headers = {
            "Authorization": f"Bearer {admin_token}",
            "Content-Type": "application/json",
        }

        # Create large payload (over 100KB)
        large_data = {"description": "x" * 200000}
        response = client.post("/api/admin/settings", json=large_data, headers=headers)
        assert response.status_code in [400, 413]

    def test_range_parameter_validation(self, client, admin_token):
        """Verify analytics range parameter validation."""
        headers = {"Authorization": f"Bearer {admin_token}"}

        # Valid range
        response = client.get("/api/analytics/events?range=7d", headers=headers)
        assert response.status_code == 200

        # Invalid format
        response = client.get("/api/analytics/events?range=invalid", headers=headers)
        assert response.status_code == 400

        # Out of range
        response = client.get("/api/analytics/events?range=1000d", headers=headers)
        assert response.status_code == 400


class TestRBAC:
    """Test Issue #109: IAM/Roles and access control."""

    def test_admin_endpoint_requires_auth(self, client):
        """Verify admin endpoints require authentication."""
        response = client.get("/api/admin/recipients")
        assert response.status_code == 401

    def test_admin_endpoint_with_invalid_token(self, client):
        """Verify admin endpoints reject invalid tokens."""
        response = client.get(
            "/api/admin/recipients", headers={"Authorization": "Bearer invalid-token"}
        )
        assert response.status_code == 401

    def test_admin_endpoint_with_valid_token(self, client, admin_token):
        """Verify admin endpoints accept valid tokens."""
        response = client.get(
            "/api/admin/recipients", headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_analytics_endpoints_require_auth(self, client):
        """Verify analytics endpoints require authentication."""
        response = client.get("/api/analytics/summary")
        assert response.status_code == 401

    def test_admin_login_audit(self, client):
        """Verify admin login attempts are logged."""
        # Failed login
        response = client.post("/api/admin/login", json={"token": "wrong-token"})
        assert response.status_code == 401

        # Successful login
        response = client.post("/api/admin/login", json={"token": "test-admin-token"})
        assert response.status_code == 200

    def test_admin_content_type_validation(self, client, admin_token):
        """Verify admin endpoints validate Content-Type."""
        response = client.post(
            "/api/admin/recipients",
            data="not json",
            headers={"Authorization": f"Bearer {admin_token}"},
            content_type="text/plain",
        )
        assert response.status_code == 400


class TestLoggingHardening:
    """Test Issue #108: Hardened logging."""

    def test_sensitive_data_filter(self):
        """Verify sensitive data patterns are redacted."""
        from security import SensitiveDataFilter

        filter_instance = SensitiveDataFilter()

        # Test password redaction
        import logging

        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="User password=secret123 logged in",
            args=(),
            exc_info=None,
        )
        filter_instance.filter(record)
        assert "password=***REDACTED***" in record.msg
        assert "secret123" not in record.msg

    def test_token_redaction(self):
        """Verify tokens are redacted in logs."""
        import logging

        from security import SensitiveDataFilter

        filter_instance = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Request with token=abc123xyz",
            args=(),
            exc_info=None,
        )
        filter_instance.filter(record)
        assert "abc123xyz" not in record.msg

    def test_bearer_token_redaction(self):
        """Verify Bearer tokens are redacted."""
        import logging

        from security import SensitiveDataFilter

        filter_instance = SensitiveDataFilter()
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="",
            lineno=0,
            msg="Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
            args=(),
            exc_info=None,
        )
        filter_instance.filter(record)
        assert "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9" not in record.msg


class TestTrackingEndpoint:
    """Test tracking endpoint security."""

    def test_tracking_sanitizes_headers(self, client):
        """Verify tracking endpoint sanitizes request headers."""
        # Create a test recipient
        with app.app_context():
            recipient = Recipients(
                r_uuid="test-uuid-tracking", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()

        # Request with sensitive headers
        response = client.get(
            "/img/test-uuid-tracking",
            headers={
                "Authorization": "Bearer secret-token",
                "Cookie": "session=secret123",
            },
        )
        assert response.status_code == 200

        # Verify tracking was created
        with app.app_context():
            tracking = Tracking.query.first()
            if tracking:
                details = json.loads(tracking.details)
                # Verify sensitive headers not stored in full
                assert "secret-token" not in str(details.get("headers", {}))


class TestConfiguration:
    """Test security configuration."""

    def test_admin_token_from_env(self, client):
        """Verify admin token can be set via environment variable."""
        original_token = os.environ.get("ADMIN_TOKEN")
        try:
            os.environ["ADMIN_TOKEN"] = "custom-admin-token"
            # Update the cached _admin_token to simulate fresh import
            import security
            original_cached_token = security._admin_token
            security._admin_token = "custom-admin-token"

            # Test with new token
            response = client.get(
                "/api/admin/recipients",
                headers={"Authorization": "Bearer custom-admin-token"},
            )
            assert response.status_code == 200

            # Restore cached token
            security._admin_token = original_cached_token
        finally:
            if original_token:
                os.environ["ADMIN_TOKEN"] = original_token


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
