"""
OIDC Provider Integration Module

This module provides OpenID Connect (OIDC) provider functionality including:
- OIDC provider configuration
- Token exchange and validation
- JWT verification middleware
- Health check endpoint for OIDC status
"""

from __future__ import annotations

import os
import time
from datetime import datetime, timedelta, timezone
from functools import wraps
from typing import Any, Callable

import jwt
from flask import Flask, json, request, jsonify
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend


class OIDCProvider:
    """OIDC Provider configuration and management."""

    def __init__(self, app: Flask | None = None) -> None:
        """Initialise OIDC provider."""
        self.app = app
        self.issuer = os.environ.get("OIDC_ISSUER", "https://readreceipt.local")
        self.jwks_uri = os.environ.get("OIDC_JWKS_URI", "/.well-known/jwks.json")
        self.authorization_endpoint = os.environ.get(
            "OIDC_AUTHORIZATION_ENDPOINT", "/oauth2/authorize"
        )
        self.token_endpoint = os.environ.get(
            "OIDC_TOKEN_ENDPOINT", "/oauth2/token"
        )
        self.userinfo_endpoint = os.environ.get(
            "OIDC_USERINFO_ENDPOINT", "/oauth2/userinfo"
        )
        self.scopes_supported = os.environ.get(
            "OIDC_SCOPES", "openid profile email"
        ).split()
        self.response_types_supported = ["code", "token", "id_token"]
        self.grant_types_supported = [
            "authorization_code",
            "refresh_token",
            "client_credentials",
        ]
        self.token_expiry_seconds = int(
            os.environ.get("OIDC_TOKEN_EXPIRY", "3600")
        )
        self.refresh_token_expiry_seconds = int(
            os.environ.get("OIDC_REFRESH_TOKEN_EXPIRY", "86400")
        )

        # Generate RSA key pair for JWT signing
        self._private_key = rsa.generate_private_key(
            public_exponent=65537, key_size=2048, backend=default_backend()
        )
        self._public_key = self._private_key.public_key()

        # In-memory token storage (replace with database in production)
        self._tokens: dict[str, dict[str, Any]] = {}
        self._refresh_tokens: dict[str, dict[str, Any]] = {}
        self._clients: dict[str, dict[str, Any]] = {}

        if app is not None:
            self.init_app(app)

    def init_app(self, app: Flask) -> None:
        """Initialise OIDC provider with Flask app."""
        self.app = app
        self._register_routes()

    def _register_routes(self) -> None:
        """Register OIDC discovery and token endpoints."""
        if self.app is None:
            return

        self.app.add_url_rule(
            "/.well-known/openid-configuration",
            "openid_configuration",
            self.get_openid_configuration,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/.well-known/jwks.json",
            "jwks",
            self.get_jwks,
            methods=["GET"],
        )
        self.app.add_url_rule(
            self.authorization_endpoint,
            "authorize",
            self.authorize,
            methods=["GET", "POST"],
        )
        self.app.add_url_rule(
            self.token_endpoint,
            "token",
            self.token,
            methods=["POST"],
        )
        self.app.add_url_rule(
            self.userinfo_endpoint,
            "userinfo",
            self.userinfo,
            methods=["GET"],
        )
        self.app.add_url_rule(
            "/api/oidc/health",
            "oidc_health",
            self.health_check,
            methods=["GET"],
        )

    def get_openid_configuration(self) -> Any:
        """Return OIDC provider configuration."""
        config = {
            "issuer": self.issuer,
            "authorization_endpoint": f"{self.issuer}{self.authorization_endpoint}",
            "token_endpoint": f"{self.issuer}{self.token_endpoint}",
            "userinfo_endpoint": f"{self.issuer}{self.userinfo_endpoint}",
            "jwks_uri": f"{self.issuer}{self.jwks_uri}",
            "scopes_supported": self.scopes_supported,
            "response_types_supported": self.response_types_supported,
            "grant_types_supported": self.grant_types_supported,
            "token_endpoint_auth_methods_supported": [
                "client_secret_basic",
                "client_secret_post",
            ],
            "id_token_signing_alg_values_supported": ["RS256"],
            "subject_types_supported": ["public"],
        }
        return jsonify(config), 200

    def get_jwks(self) -> Any:
        """Return JSON Web Key Set."""
        public_pem = self._public_key.public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        ).decode("utf-8")

        jwks = {
            "keys": [
                {
                    "kty": "RSA",
                    "use": "sig",
                    "kid": "readreceipt-oidc-key-1",
                    "alg": "RS256",
                    "n": jwt.utils.base64url_encode(
                        self._public_key.public_numbers().n.to_bytes(
                            (self._public_key.public_numbers().n.bit_length() + 7) // 8,
                            "big",
                        )
                    ).decode("utf-8"),
                    "e": jwt.utils.base64url_encode(
                        self._public_key.public_numbers().e.to_bytes(
                            (self._public_key.public_numbers().e.bit_length() + 7) // 8,
                            "big",
                        )
                    ).decode("utf-8"),
                }
            ]
        }
        return jsonify(jwks), 200

    def register_client(
        self,
        client_id: str,
        client_secret: str,
        redirect_uris: list[str],
        grant_types: list[str] | None = None,
    ) -> None:
        """Register an OIDC client."""
        self._clients[client_id] = {
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uris": redirect_uris,
            "grant_types": grant_types or ["authorization_code"],
        }

    def authorize(self) -> Any:
        """Handle authorization request."""
        client_id = request.args.get("client_id") or request.form.get("client_id")
        redirect_uri = request.args.get("redirect_uri") or request.form.get(
            "redirect_uri"
        )
        response_type = request.args.get("response_type") or request.form.get(
            "response_type"
        )
        scope = request.args.get("scope") or request.form.get("scope", "openid")
        state = request.args.get("state") or request.form.get("state")
        nonce = request.args.get("nonce") or request.form.get("nonce")

        if not client_id or not redirect_uri or not response_type:
            return jsonify({"error": "invalid_request", "error_description": "Missing required parameters"}), 400

        if client_id not in self._clients:
            return jsonify({"error": "invalid_client"}), 400

        client = self._clients[client_id]
        if redirect_uri not in client["redirect_uris"]:
            return jsonify({"error": "invalid_redirect_uri"}), 400

        # Generate authorization code
        auth_code = f"auth_{os.urandom(32).hex()}"
        self._tokens[auth_code] = {
            "type": "authorization_code",
            "client_id": client_id,
            "scope": scope,
            "nonce": nonce,
            "created_at": time.time(),
        }

        # Redirect back with authorization code
        redirect_params = {"code": auth_code}
        if state:
            redirect_params["state"] = state

        query_string = "&".join(f"{k}={v}" for k, v in redirect_params.items())
        return jsonify({"redirect": f"{redirect_uri}?{query_string}"}), 200

    def token(self) -> Any:
        """Handle token exchange request."""
        grant_type = request.form.get("grant_type")
        client_id = request.form.get("client_id")
        client_secret = request.form.get("client_secret")

        if not grant_type:
            return jsonify({"error": "invalid_request"}), 400

        # Authenticate client
        if client_id and client_secret:
            if client_id not in self._clients:
                return jsonify({"error": "invalid_client"}), 400
            if self._clients[client_id]["client_secret"] != client_secret:
                return jsonify({"error": "invalid_client"}), 400
        else:
            # Try basic auth
            auth = request.authorization
            if auth:
                client_id = auth.username
                client_secret = auth.password
                if client_id not in self._clients:
                    return jsonify({"error": "invalid_client"}), 400
                if self._clients[client_id]["client_secret"] != client_secret:
                    return jsonify({"error": "invalid_client"}), 400

        if grant_type == "authorization_code":
            code = request.form.get("code")
            redirect_uri = request.form.get("redirect_uri")

            if not code or code not in self._tokens:
                return jsonify({"error": "invalid_grant"}), 400

            token_data = self._tokens[code]
            if token_data["type"] != "authorization_code":
                return jsonify({"error": "invalid_grant"}), 400

            # Remove used code
            del self._tokens[code]

            return self._generate_token_response(
                client_id, token_data["scope"], token_data.get("nonce")
            )

        elif grant_type == "refresh_token":
            refresh_token = request.form.get("refresh_token")

            if not refresh_token or refresh_token not in self._refresh_tokens:
                return jsonify({"error": "invalid_grant"}), 400

            refresh_data = self._refresh_tokens[refresh_token]
            if refresh_data["client_id"] != client_id:
                return jsonify({"error": "invalid_grant"}), 400

            # Remove old refresh token
            del self._refresh_tokens[refresh_token]

            return self._generate_token_response(
                client_id, refresh_data["scope"], include_refresh=True
            )

        elif grant_type == "client_credentials":
            return self._generate_token_response(client_id, "client", include_refresh=False)

        return jsonify({"error": "unsupported_grant_type"}), 400

    def _generate_token_response(
        self,
        client_id: str,
        scope: str,
        nonce: str | None = None,
        include_refresh: bool = True,
    ) -> Any:
        """Generate access token and ID token."""
        now = datetime.now(timezone.utc)
        expires_at = now + timedelta(seconds=self.token_expiry_seconds)

        # Generate access token
        access_token_payload = {
            "iss": self.issuer,
            "sub": f"user_{client_id}",
            "aud": client_id,
            "exp": expires_at,
            "iat": now,
            "scope": scope,
        }

        access_token = jwt.encode(
            access_token_payload,
            self._private_key,
            algorithm="RS256",
        )

        response: dict[str, Any] = {
            "access_token": access_token,
            "token_type": "Bearer",
            "expires_in": self.token_expiry_seconds,
        }

        # Generate ID token for OIDC flows
        if "openid" in scope or nonce:
            id_token_payload = {
                "iss": self.issuer,
                "sub": f"user_{client_id}",
                "aud": client_id,
                "exp": expires_at,
                "iat": now,
            }
            if nonce:
                id_token_payload["nonce"] = nonce

            id_token = jwt.encode(
                id_token_payload,
                self._private_key,
                algorithm="RS256",
            )
            response["id_token"] = id_token

        # Generate refresh token
        if include_refresh:
            refresh_token = f"refresh_{os.urandom(32).hex()}"
            self._refresh_tokens[refresh_token] = {
                "client_id": client_id,
                "scope": scope,
                "created_at": time.time(),
            }
            response["refresh_token"] = refresh_token

        return jsonify(response), 200

    def userinfo(self) -> Any:
        """Return user information."""
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "unauthorized"}), 401

        token = auth_header[7:]
        try:
            payload = jwt.decode(
                token,
                self._public_key,
                algorithms=["RS256"],
                audience=self._clients.keys() if self._clients else None,
            )

            return jsonify({
                "sub": payload.get("sub"),
                "name": f"User {payload.get('sub')}",
                "email": f"{payload.get('sub')}@readreceipt.local",
            }), 200
        except jwt.InvalidTokenError:
            return jsonify({"error": "invalid_token"}), 401

    def health_check(self) -> Any:
        """Check OIDC provider health status."""
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "components": {
                "issuer_configured": bool(self.issuer),
                "jwks_available": True,
                "keys_generated": self._private_key is not None,
                "clients_registered": len(self._clients),
                "active_tokens": len(self._tokens),
                "active_refresh_tokens": len(self._refresh_tokens),
            },
            "endpoints": {
                "openid_configuration": f"{self.issuer}/.well-known/openid-configuration",
                "jwks_uri": f"{self.issuer}/.well-known/jwks.json",
                "authorization": f"{self.issuer}{self.authorization_endpoint}",
                "token": f"{self.issuer}{self.token_endpoint}",
                "userinfo": f"{self.issuer}{self.userinfo_endpoint}",
            },
        }
        return jsonify(health_status), 200


def jwt_verification_required(
    oidc_provider: OIDCProvider,
) -> Callable[[Callable], Callable]:
    """Decorator to require JWT verification on endpoints."""

    def decorator(f: Callable) -> Callable:
        @wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            auth_header = request.headers.get("Authorization", "")
            if not auth_header.startswith("Bearer "):
                return jsonify({"error": "unauthorized", "message": "Missing Authorization header"}), 401

            token = auth_header[7:]
            try:
                # Verify JWT token
                payload = jwt.decode(
                    token,
                    oidc_provider._public_key,
                    algorithms=["RS256"],
                    issuer=oidc_provider.issuer,
                    options={"verify_aud": False},  # Optional: validate audience if needed
                )
                # Attach decoded payload to request context
                request.oidc_payload = payload  # type: ignore[attr-defined]
            except jwt.ExpiredSignatureError:
                return jsonify({"error": "token_expired"}), 401
            except jwt.InvalidTokenError as e:
                return jsonify({"error": "invalid_token", "message": str(e)}), 401

            return f(*args, **kwargs)

        return decorated_function

    return decorator


# Helper function to validate tokens
def validate_token(token: str, oidc_provider: OIDCProvider) -> dict[str, Any] | None:
    """Validate an OIDC token and return its payload."""
    try:
        payload = jwt.decode(
            token,
            oidc_provider._public_key,
            algorithms=["RS256"],
            issuer=oidc_provider.issuer,
            options={"verify_aud": False},
        )
        return payload
    except jwt.InvalidTokenError:
        return None
