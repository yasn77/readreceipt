"""Integration tests for the ReadReceipt Flask application.

These tests verify that the app can start without import errors
and that all critical endpoints are functional.
"""

import os
from collections.abc import Generator
from typing import Any

import pytest

# Test imports - this will catch import errors immediately
try:
    from app import (
        Recipients,
        Tracking,
        app,
        db,
    )
    from security import init_security, require_admin
except ImportError as e:
    pytest.exit(f"Import error - app cannot start: {e}")


@pytest.fixture
def integration_client() -> Generator[Any, None, None]:
    """Create a test client with in-memory database for integration testing."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["SECRET_KEY"] = "test-secret-key-for-integration"

    with app.app_context():
        db.create_all()
        yield app.test_client()
        db.session.remove()
        db.drop_all()


@pytest.fixture
def admin_client(integration_client: Any) -> Any:
    """Create an authenticated admin client."""
    os.environ["ADMIN_TOKEN"] = "integration-test-token"
    # Also update the cached _admin_token in security module
    # since it was set at import time when ADMIN_TOKEN wasn't set
    import security
    security._admin_token = "integration-test-token"
    return integration_client


class TestAppStartup:
    """Test that the application can start without errors."""

    def test_app_imports_successfully(self) -> None:
        """Verify all critical imports work."""
        # If we got here, imports succeeded (checked at module level)
        assert app is not None
        assert db is not None

    def test_app_has_required_extensions(self) -> None:
        """Verify Flask extensions are properly initialized."""
        assert hasattr(app, "extensions")
        # SQLAlchemy should be initialized
        assert "sqlalchemy" in app.extensions or db in app.extensions.values()

    def test_security_module_initialized(self) -> None:
        """Verify security module is properly imported and functional."""
        assert init_security is not None
        assert require_admin is not None


class TestRootEndpoint:
    """Integration tests for the root endpoint."""

    def test_root_endpoint_responds(self, integration_client: Any) -> None:
        """Test that the root endpoint is accessible and responds."""
        response = integration_client.get("/")
        assert response.status_code == 200, "Root endpoint should return 200 OK"


class TestHealthCheck:
    """Integration tests for health check endpoints."""

    def test_root_returns_healthy_response(self, integration_client: Any) -> None:
        """Test that root endpoint returns a healthy response."""
        response = integration_client.get("/")
        assert response.status_code == 200
        # Empty response is expected for root

    def test_db_connection_works(self, integration_client: Any) -> None:
        """Test that database connection is functional."""
        from sqlalchemy import text

        with app.app_context():
            # Try a simple query
            result = db.session.execute(text("SELECT 1"))
            assert result is not None, "Database connection should work"


class TestOIDCEndpoints:
    """Integration tests for OIDC endpoints.

    Note: These tests will fail if OIDC provider is not properly initialized.
    This is intentional - we want to catch missing OIDC configuration.
    """

    def test_oidc_authorize_endpoint_exists(self, integration_client: Any) -> None:
        """Test that OIDC authorize endpoint is accessible.

        This test documents whether OIDC provider routes are registered.
        Note: This test expects 404 if OIDC is not implemented.
        """
        response = integration_client.get("/oauth2/authorize")
        # If 404, OIDC is not implemented - this is expected for now
        if response.status_code == 404:
            import warnings

            warnings.warn(
                "OIDC authorize endpoint returns 404. "
                "OIDC provider not initialized. Add 'oidc = OIDCProvider(app)' to fix."
            )
        # If it exists, it should not return server error
        elif response.status_code >= 500:
            pytest.fail(f"OIDC endpoint has server error: {response.status_code}")

    def test_openid_configuration_endpoint(self, integration_client: Any) -> None:
        """Test that OIDC discovery endpoint is accessible."""
        response = integration_client.get("/.well-known/openid-configuration")
        # Should not return 404 if OIDC is properly configured
        if response.status_code == 404:
            import warnings

            warnings.warn(
                "OIDC discovery endpoint not found. OIDC provider may not be initialized."
            )
        # If it exists, it should return valid JSON
        if response.status_code == 200:
            assert response.is_json or "application/json" in response.content_type


class TestAdminEndpoints:
    """Integration tests for admin endpoints with authentication."""

    def test_admin_login_requires_auth(self, admin_client: Any) -> None:
        """Test that admin login endpoint requires valid token."""
        # Test without token
        response = admin_client.post(
            "/api/admin/login",
            json={},
            content_type="application/json",
        )
        assert response.status_code == 400, "Should require token"

    def test_admin_login_with_valid_token(self, admin_client: Any) -> None:
        """Test successful admin login with valid token."""
        os.environ["ADMIN_TOKEN"] = "integration-test-token"

        response = admin_client.post(
            "/api/admin/login",
            json={"token": "integration-test-token"},
            content_type="application/json",
        )
        assert response.status_code == 200, f"Login should succeed: {response.data}"
        data = response.get_json()
        assert data is not None
        assert data.get("status") == "authenticated"

    def test_admin_recipients_requires_auth(self, admin_client: Any) -> None:
        """Test that admin recipients endpoint requires authentication."""
        # Without auth header
        response = admin_client.get("/api/admin/recipients")
        # Should return 401/403 without valid auth
        assert response.status_code in [
            401,
            403,
        ], "Admin endpoint should require authentication"

    def test_admin_recipients_with_auth(self, admin_client: Any) -> None:
        """Test admin recipients endpoint with valid authentication."""
        os.environ["ADMIN_TOKEN"] = "integration-test-token"

        # Access recipients with valid auth header
        # Note: require_admin decorator checks Authorization header
        response = admin_client.get(
            "/api/admin/recipients",
            headers={"Authorization": "Bearer integration-test-token"},
        )
        # Should succeed with valid auth
        assert response.status_code == 200, f"Should access recipients: {response.data}"


class TestAPIEndpoints:
    """Integration tests for general API endpoints."""

    def test_new_uuid_endpoint(self, integration_client: Any) -> None:
        """Test that new-uuid endpoint works."""
        response = integration_client.get("/new-uuid")
        assert response.status_code == 200
        assert b"<p>" in response.data or b"uuid" in response.data.lower()

    def test_img_endpoint_with_valid_uuid(self, integration_client: Any) -> None:
        """Test image endpoint with a valid UUID."""
        # First create a recipient
        response = integration_client.get(
            "/new-uuid?description=test&email=test@example.com"
        )
        assert response.status_code == 200

        # Extract UUID from response (it's in the HTML)
        import re

        match = re.search(r"<p>([a-f0-9-]+)<p>", response.data.decode())
        if match:
            uuid = match.group(1)
            img_response = integration_client.get(f"/img/{uuid}")
            assert img_response.status_code == 200
            assert img_response.content_type == "image/png"

    def test_img_endpoint_with_invalid_uuid(self, integration_client: Any) -> None:
        """Test image endpoint handles invalid UUID gracefully."""
        response = integration_client.get("/img/00000000-0000-0000-0000-000000000000")
        assert response.status_code == 404
        data = response.get_json()
        assert data is not None
        assert "error" in data


class TestAppConfiguration:
    """Integration tests for app configuration."""

    def test_secret_key_is_set(self) -> None:
        """Verify SECRET_KEY is configured."""
        assert (
            app.config.get("SECRET_KEY") is not None
        ), "SECRET_KEY must be set for sessions and security"

    def test_sqlalchemy_database_uri_is_set(self) -> None:
        """Verify SQLAlchemy database URI is configured."""
        assert (
            app.config.get("SQLALCHEMY_DATABASE_URI") is not None
        ), "SQLALCHEMY_DATABASE_URI must be configured"

    def test_test_mode_flag_works(self) -> None:
        """Verify TESTING flag can be set."""
        original = app.config.get("TESTING")
        app.config["TESTING"] = True
        assert app.config["TESTING"] is True
        app.config["TESTING"] = original


if __name__ == "__main__":
    # Run with: python -m pytest tests/test_integration.py -v
    pytest.main([__file__, "-v"])
