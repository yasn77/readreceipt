"""Tests for OIDC provider integration."""

from __future__ import annotations

from collections.abc import Generator

import pytest
from flask.testing import FlaskClient

from readreceipt.app import app


@pytest.fixture
def client() -> Generator[FlaskClient, None, None]:
    """Create test client."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        yield client


class TestOpenIDConfiguration:
    """Test OIDC discovery endpoint."""

    def test_openid_configuration_endpoint(self, client: FlaskClient) -> None:
        """Test that OIDC configuration is exposed."""
        response = client.get("/.well-known/openid-configuration")
        assert response.status_code == 200
        data = response.get_json()
        assert "issuer" in data
        assert "authorization_endpoint" in data
        assert "token_endpoint" in data
        assert "jwks_uri" in data
        assert "scopes_supported" in data

    def test_jwks_endpoint(self, client: FlaskClient) -> None:
        """Test that JWKS endpoint returns valid keys."""
        response = client.get("/.well-known/jwks.json")
        assert response.status_code == 200
        data = response.get_json()
        assert "keys" in data
        assert len(data["keys"]) > 0
        key = data["keys"][0]
        assert key["kty"] == "RSA"
        assert key["alg"] == "RS256"


class TestAuthorizationEndpoint:
    """Test authorization endpoint."""

    def test_authorize_missing_params(self, client: FlaskClient) -> None:
        """Test authorization with missing parameters."""
        response = client.get("/oauth2/authorize")
        assert response.status_code == 400
        data = response.get_json()
        assert "error" in data

    def test_authorize_invalid_client(self, client: FlaskClient) -> None:
        """Test authorization with invalid client."""
        response = client.get(
            "/oauth2/authorize?client_id=invalid&redirect_uri=http://example.com&response_type=code"
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_client"

    def test_authorize_success(self, client: FlaskClient) -> None:
        """Test successful authorization request."""
        response = client.get(
            "/oauth2/authorize?client_id=readreceipt-admin&redirect_uri=http://localhost:3000/callback&response_type=code&scope=openid&state=test123"
        )
        assert response.status_code == 200
        data = response.get_json()
        assert "redirect" in data
        assert "code=" in data["redirect"]


class TestTokenEndpoint:
    """Test token endpoint."""

    def test_token_missing_grant_type(self, client: FlaskClient) -> None:
        """Test token request without grant type."""
        response = client.post("/oauth2/token", data={})
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_request"

    def test_token_invalid_client(self, client: FlaskClient) -> None:
        """Test token request with invalid client."""
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "client_id": "invalid",
                "client_secret": "invalid",
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_client"

    def test_token_invalid_code(self, client: FlaskClient) -> None:
        """Test token request with invalid authorization code."""
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": "invalid",
                "client_id": "readreceipt-admin",
                "client_secret": "admin-secret",
            },
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["error"] == "invalid_grant"


class TestUserinfoEndpoint:
    """Test userinfo endpoint."""

    def test_userinfo_no_token(self, client: FlaskClient) -> None:
        """Test userinfo without token."""
        response = client.get("/oauth2/userinfo")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "unauthorized"

    def test_userinfo_invalid_token(self, client: FlaskClient) -> None:
        """Test userinfo with invalid token."""
        response = client.get(
            "/oauth2/userinfo",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_token"


class TestHealthEndpoint:
    """Test OIDC health check endpoint."""

    def test_health_check(self, client: FlaskClient) -> None:
        """Test OIDC health check returns status."""
        response = client.get("/api/oidc/health")
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
        assert "components" in data
        assert "endpoints" in data

    def test_health_check_components(self, client: FlaskClient) -> None:
        """Test health check includes all components."""
        response = client.get("/api/oidc/health")
        data = response.get_json()
        components = data["components"]
        assert "issuer_configured" in components
        assert "jwks_available" in components
        assert "keys_generated" in components
        assert "clients_registered" in components


class TestProtectedEndpoint:
    """Test protected endpoints with JWT verification."""

    def test_protected_no_auth(self, client: FlaskClient) -> None:
        """Test protected endpoint without authentication."""
        response = client.get("/api/admin/protected")
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "unauthorized"

    def test_protected_invalid_token(self, client: FlaskClient) -> None:
        """Test protected endpoint with invalid token."""
        response = client.get(
            "/api/admin/protected",
            headers={"Authorization": "Bearer invalid_token"},
        )
        assert response.status_code == 401
        data = response.get_json()
        assert data["error"] == "invalid_token"


class TestOIDCClientRegistration:
    """Test OIDC client registration."""

    def test_client_registered(self, client: FlaskClient) -> None:
        """Test that demo client is registered."""
        response = client.get("/api/oidc/health")
        data = response.get_json()
        assert data["components"]["clients_registered"] >= 1


@pytest.fixture
def auth_code_flow_client() -> Generator[tuple[FlaskClient, dict], None, None]:
    """Test client for full auth code flow."""
    app.config["TESTING"] = True
    with app.test_client() as client:
        # Step 1: Get authorization code
        auth_response = client.get(
            "/oauth2/authorize?client_id=readreceipt-admin&redirect_uri=http://localhost:3000/callback&response_type=code&scope=openid"
        )
        auth_data = auth_response.get_json()
        assert "redirect" in auth_data

        # Extract code from redirect
        redirect_url = auth_data["redirect"]
        code = redirect_url.split("code=")[1].split("&")[0]

        # Step 2: Exchange code for token
        token_response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "authorization_code",
                "code": code,
                "redirect_uri": "http://localhost:3000/callback",
                "client_id": "readreceipt-admin",
                "client_secret": "admin-secret",
            },
        )
        token_data = token_response.get_json()

        yield (client, token_data)


class TestFullAuthCodeFlow:
    """Test complete authorization code flow."""

    def test_full_auth_code_flow(
        self, auth_code_flow_client: tuple[FlaskClient, dict]
    ) -> None:
        """Test complete OIDC authorization code flow."""
        client, token_data = auth_code_flow_client

        # Verify token response
        assert "access_token" in token_data
        assert token_data["token_type"] == "Bearer"
        assert "expires_in" in token_data
        assert "id_token" in token_data
        assert "refresh_token" in token_data

        # Use access token to access protected resource
        access_token = token_data["access_token"]
        protected_response = client.get(
            "/api/admin/protected",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert protected_response.status_code == 200
        protected_data = protected_response.get_json()
        assert protected_data["status"] == "access_granted"
        assert "user" in protected_data

    def test_refresh_token_flow(
        self, auth_code_flow_client: tuple[FlaskClient, dict]
    ) -> None:
        """Test token refresh flow."""
        client, token_data = auth_code_flow_client

        refresh_token = token_data["refresh_token"]

        # Use refresh token to get new access token
        refresh_response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "refresh_token",
                "refresh_token": refresh_token,
                "client_id": "readreceipt-admin",
                "client_secret": "admin-secret",
            },
        )

        assert refresh_response.status_code == 200
        new_token_data = refresh_response.get_json()
        assert "access_token" in new_token_data
        assert "refresh_token" in new_token_data  # New refresh token


class TestClientCredentialsFlow:
    """Test client credentials grant type."""

    def test_client_credentials_grant(self, client: FlaskClient) -> None:
        """Test client credentials flow."""
        response = client.post(
            "/oauth2/token",
            data={
                "grant_type": "client_credentials",
                "client_id": "readreceipt-admin",
                "client_secret": "admin-secret",
            },
        )

        assert response.status_code == 200
        token_data = response.get_json()
        assert "access_token" in token_data
        assert "id_token" not in token_data  # No ID token for client credentials
        # No refresh token for client credentials
        assert "refresh_token" not in token_data
