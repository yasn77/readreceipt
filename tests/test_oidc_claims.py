"""Tests for OIDC claims mapping and admin role management."""

import json
import os
import unittest

from app import (
    AdminUser,
    AuditLog,
    app,
    db,
    extract_claims_from_token,
    map_claims_to_admin_roles,
)


class TestOIDCClaimsMapping(unittest.TestCase):
    """Test OIDC claims extraction and mapping."""

    def setUp(self):
        """Set up test fixtures."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["OIDC_ALLOWED_EMAILS"] = [
            "admin@example.com",
            "superuser@example.com",
        ]
        app.config["OIDC_ADMIN_ROLES"] = ["admin", "superuser"]

        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after tests."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_extract_claims_from_token(self):
        """Test extracting claims from OIDC token."""
        token = {
            "sub": "1234567890",
            "email": "user@example.com",
            "email_verified": True,
            "name": "Test User",
            "roles": ["admin", "user"],
            "groups": ["admins", "developers"],
            "iss": "https://auth.example.com",
            "aud": "readreceipt-app",
        }

        claims = extract_claims_from_token(token)

        self.assertEqual(claims["sub"], "1234567890")
        self.assertEqual(claims["email"], "user@example.com")
        self.assertTrue(claims["email_verified"])
        self.assertEqual(claims["name"], "Test User")
        self.assertEqual(claims["roles"], ["admin", "user"])
        self.assertEqual(claims["groups"], ["admins", "developers"])

    def test_map_claims_to_admin_roles_with_roles(self):
        """Test mapping roles from token claims."""
        claims = {
            "email": "user@example.com",
            "roles": ["admin", "user"],
        }

        roles = map_claims_to_admin_roles(claims)

        self.assertIn("admin", roles)
        self.assertNotIn("user", roles)  # 'user' is not an admin role

    def test_map_claims_to_admin_roles_with_groups(self):
        """Test mapping groups to admin roles."""
        claims = {
            "email": "user@example.com",
            "groups": ["admins", "developers"],
        }

        roles = map_claims_to_admin_roles(claims)

        self.assertIn("admin", roles)

    def test_map_claims_to_admin_roles_with_email_whitelist(self):
        """Test email whitelist grants admin access."""
        claims = {
            "email": "admin@example.com",
            "roles": [],
        }

        roles = map_claims_to_admin_roles(claims)

        self.assertIn("admin", roles)

    def test_map_claims_to_admin_roles_no_access(self):
        """Test user with no admin roles gets no access."""
        claims = {
            "email": "regular@example.com",
            "roles": ["user"],
            "groups": ["developers"],
        }

        roles = map_claims_to_admin_roles(claims)

        self.assertEqual(roles, [])


class TestAdminUserModel(unittest.TestCase):
    """Test AdminUser model functionality."""

    def setUp(self):
        """Set up test fixtures."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret-key"

        self.app = app
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after tests."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_admin_user(self):
        """Test creating an admin user."""
        user = AdminUser(
            email="admin@example.com",
            oidc_sub="1234567890",
            roles=["admin"],
        )
        db.session.add(user)
        db.session.commit()

        found_user = AdminUser.query.filter_by(email="admin@example.com").first()

        self.assertIsNotNone(found_user)
        self.assertEqual(found_user.oidc_sub, "1234567890")
        self.assertEqual(found_user.roles, ["admin"])
        self.assertTrue(found_user.is_active)

    def test_admin_user_has_role(self):
        """Test checking if user has a specific role."""
        user = AdminUser(
            email="admin@example.com",
            oidc_sub="1234567890",
            roles=["admin", "superuser"],
        )

        self.assertTrue(user.has_role("admin"))
        self.assertTrue(user.has_role("superuser"))
        self.assertFalse(user.has_role("user"))

    def test_admin_user_to_dict(self):
        """Test converting admin user to dictionary."""
        user = AdminUser(
            email="admin@example.com",
            oidc_sub="1234567890",
            roles=["admin"],
        )
        db.session.add(user)
        db.session.commit()

        user_dict = user.to_dict()

        self.assertEqual(user_dict["email"], "admin@example.com")
        self.assertEqual(user_dict["roles"], ["admin"])
        self.assertTrue(user_dict["is_active"])
        self.assertIn("id", user_dict)
        self.assertIn("created_at", user_dict)


class TestAuditLog(unittest.TestCase):
    """Test AuditLog model functionality."""

    def setUp(self):
        """Set up test fixtures."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret-key"

        self.app = app
        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after tests."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_create_audit_log(self):
        """Test creating an audit log entry."""
        user = AdminUser(
            email="admin@example.com",
            oidc_sub="1234567890",
            roles=["admin"],
        )
        db.session.add(user)
        db.session.commit()

        log = AuditLog(
            admin_user_id=user.id,
            action="login",
            details={"ip": "192.168.1.1"},
            ip_address="192.168.1.1",
            user_agent="Test Browser",
        )
        db.session.add(log)
        db.session.commit()

        found_log = AuditLog.query.first()

        self.assertIsNotNone(found_log)
        self.assertEqual(found_log.action, "login")
        self.assertEqual(found_log.admin_user_id, user.id)
        self.assertEqual(found_log.ip_address, "192.168.1.1")


class TestOIDCAuthEndpoints(unittest.TestCase):
    """Test OIDC authentication endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        app.config["TESTING"] = True
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["SECRET_KEY"] = "test-secret-key"
        app.config["OIDC_DISCOVERY_URL"] = (
            "https://auth.example.com/.well-known/openid-configuration"
        )
        app.config["OIDC_CLIENT_ID"] = "test-client-id"
        app.config["OIDC_CLIENT_SECRET"] = "test-secret"
        app.config["OIDC_ALLOWED_EMAILS"] = ["admin@example.com"]
        app.config["OIDC_ADMIN_ROLES"] = ["admin"]

        self.app = app
        self.client = app.test_client()

        with app.app_context():
            db.create_all()

    def tearDown(self):
        """Clean up after tests."""
        with app.app_context():
            db.session.remove()
            db.drop_all()

    def test_get_current_user_not_authenticated(self):
        """Test getting current user when not authenticated."""
        response = self.client.get("/api/auth/me")

        self.assertEqual(response.status_code, 401)
        data = json.loads(response.data)
        self.assertFalse(data["authenticated"])

    def test_admin_login_token_auth(self):
        """Test legacy token authentication."""
        os.environ["ADMIN_TOKEN"] = "test-token"
        # Update cached _admin_token in security module
        import security
        security._admin_token = "test-token"

        response = self.client.post(
            "/api/admin/login",
            json={"token": "test-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertEqual(data["status"], "authenticated")

    def test_admin_login_invalid_token(self):
        """Test login with invalid token."""
        os.environ["ADMIN_TOKEN"] = "test-token"
        # Update cached _admin_token in security module
        import security
        security._admin_token = "test-token"

        response = self.client.post(
            "/api/admin/login",
            json={"token": "wrong-token"},
            content_type="application/json",
        )

        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_requires_auth(self):
        """Test that protected endpoints require authentication."""
        response = self.client.get("/api/admin/recipients")

        self.assertEqual(response.status_code, 401)

    def test_protected_endpoint_with_valid_token(self):
        """Test accessing protected endpoint with valid token."""
        os.environ["ADMIN_TOKEN"] = "test-token"
        # Update cached _admin_token in security module
        import security
        security._admin_token = "test-token"

        response = self.client.get(
            "/api/admin/recipients", headers={"Authorization": "Bearer test-token"}
        )

        self.assertEqual(response.status_code, 200)


if __name__ == "__main__":
    unittest.main()
