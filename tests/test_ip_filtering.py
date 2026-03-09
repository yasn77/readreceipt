"""
Tests for Issue #151 - IP-based own-open filtering
"""

import os
import uuid

import pytest

from app import AdminUser, Recipients, Tracking, app, db


class TestIPBlocklistEndpoints:
    """Tests for IP blocklist management API endpoints."""

    def auth_headers(self, token="admin"):
        """Return authorization headers for admin endpoints."""
        return {"Authorization": f"Bearer {token}"}

    @pytest.fixture(autouse=True)
    def setup_test_db(self):
        """Setup fresh database for each test."""
        import tempfile
        # Use a file-based database with a unique path for proper isolation
        self.db_fd, self.db_path = tempfile.mkstemp(suffix='.db')
        app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{self.db_path}"
        app.config["TESTING"] = True
        # Set admin token environment variable
        os.environ["ADMIN_TOKEN"] = "admin"

        with app.app_context():
            db.create_all()
            yield
            db.session.remove()
            db.drop_all()

        # Cleanup
        os.close(self.db_fd)
        os.unlink(self.db_path)

    @pytest.fixture
    def admin_client(self):
        """Create test client with admin user."""
        with app.app_context():
            # Create admin user
            admin = AdminUser(
                email="admin@test.com",
                oidc_sub="test-admin-sub",
                roles=["admin"],
                ip_blocklist=[],
            )
            db.session.add(admin)
            db.session.commit()

            yield app.test_client()

    @pytest.fixture
    def sample_recipient(self):
        """Create sample recipient for tracking tests."""
        with app.app_context():
            test_uuid = str(uuid.uuid4())
            recipient = Recipients(
                r_uuid=test_uuid, description="Test", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()
            return test_uuid

    def test_get_ip_blocklist_empty(self, admin_client):
        """Test getting empty IP blocklist."""
        response = admin_client.get(
            "/api/admin/ip-blocklist", headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["ip_blocklist"] == []
        assert data["count"] == 0

    def test_add_ip_to_blocklist_ipv4(self, admin_client):
        """Test adding IPv4 address to blocklist."""
        response = admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "192.168.1.1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "added"
        assert data["ip_address"] == "192.168.1.1"
        assert data["total_blocked"] == 1

    def test_add_ip_to_blocklist_ipv6(self, admin_client):
        """Test adding IPv6 address to blocklist."""
        response = admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "2001:db8::1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 201
        data = response.get_json()
        assert data["status"] == "added"
        assert data["ip_address"] == "2001:db8::1"

    def test_add_duplicate_ip(self, admin_client):
        """Test adding duplicate IP returns 409."""
        # Add IP first
        admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "10.0.0.1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )

        # Try to add again
        response = admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "10.0.0.1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 409
        data = response.get_json()
        assert "already in blocklist" in data["error"]

    def test_add_invalid_ip_format(self, admin_client):
        """Test adding invalid IP format returns 400."""
        response = admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "not-an-ip"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert "Invalid IP address format" in data["error"]

    def test_validate_ip_endpoint(self, admin_client):
        """Test IP validation endpoint."""
        # Valid IPv4
        response = admin_client.post(
            "/api/admin/ip-blocklist/validate",
            json={"ip_address": "192.168.1.1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True
        assert data["version"] == "IPv4"

        # Valid IPv6
        response = admin_client.post(
            "/api/admin/ip-blocklist/validate",
            json={"ip_address": "2001:db8::1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["valid"] is True
        assert data["version"] == "IPv6"

        # Invalid IP
        response = admin_client.post(
            "/api/admin/ip-blocklist/validate",
            json={"ip_address": "invalid"},
            headers=self.auth_headers(),
            content_type="application/json",
        )
        assert response.status_code == 400
        data = response.get_json()
        assert data["valid"] is False

    def test_remove_ip_from_blocklist(self, admin_client):
        """Test removing IP from blocklist."""
        # Add IP first
        admin_client.post(
            "/api/admin/ip-blocklist",
            json={"ip_address": "172.16.0.1"},
            headers=self.auth_headers(),
            content_type="application/json",
        )

        # Remove it
        response = admin_client.delete(
            "/api/admin/ip-blocklist/172.16.0.1", headers=self.auth_headers()
        )
        assert response.status_code == 200
        data = response.get_json()
        assert data["status"] == "removed"
        assert data["total_blocked"] == 0

    def test_remove_nonexistent_ip(self, admin_client):
        """Test removing IP not in blocklist returns 404."""
        response = admin_client.delete(
            "/api/admin/ip-blocklist/1.2.3.4", headers=self.auth_headers()
        )
        assert response.status_code == 404
        data = response.get_json()
        assert "not in blocklist" in data["error"]


class TestIPBasedFiltering:
    """Tests for IP-based tracking filtering logic."""

    def test_tracking_blocked_when_ip_in_blocklist(self):
        """Test that tracking is blocked when requesting IP is in blocklist."""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
        app.config["TESTING"] = True

        with app.test_client() as client:
            with app.app_context():
                db.create_all()

                # Create admin user with IP blocklist
                admin = AdminUser(
                    email="admin@test.com",
                    oidc_sub="test-sub",
                    roles=["admin"],
                    ip_blocklist=["203.0.113.1", "198.51.100.1"],
                )
                db.session.add(admin)

                # Create recipient
                test_uuid = str(uuid.uuid4())
                recipient = Recipients(
                    r_uuid=test_uuid, description="Test", email="test@example.com"
                )
                db.session.add(recipient)
                db.session.commit()

            # Make request with blocked IP (via X-Forwarded-For)
            response = client.get(
                f"/img/{test_uuid}",
                headers={
                    "X-Forwarded-For": "203.0.113.1",
                    "User-Agent": "Mozilla/5.0 Test",
                },
                base_url="http://local.test",
            )
            assert response.status_code == 200

            # Verify tracking was NOT recorded
            with app.app_context():
                tracking_count = Tracking.query.count()
                assert (
                    tracking_count == 0
                ), "Tracking should be blocked for IP in blocklist"

    def test_tracking_allowed_when_ip_not_in_blocklist(self):
        """Test that tracking is allowed when IP is not in blocklist."""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:?check_same_thread=False"
        app.config["TESTING"] = True

        with app.app_context():
            db.create_all()

            # Create admin user with IP blocklist (use unique email)
            admin = AdminUser(
                email="allowed@test.com",
                oidc_sub="test-sub-allowed",
                roles=["admin"],
                ip_blocklist=["203.0.113.1"],
            )
            db.session.add(admin)

            # Create recipient
            test_uuid = str(uuid.uuid4())
            recipient = Recipients(
                r_uuid=test_uuid, description="Test", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()

            with app.test_client() as client:
                # Make request with different IP
                response = client.get(
                    f"/img/{test_uuid}",
                    headers={
                        "X-Forwarded-For": "8.8.8.8",
                        "User-Agent": "Mozilla/5.0 Test",
                    },
                    base_url="http://local.test",
                )
                assert response.status_code == 200

                # Verify tracking WAS recorded
                tracking_count = Tracking.query.count()
                assert (
                    tracking_count == 1
                ), "Tracking should be recorded for IP not in blocklist"

            db.session.remove()
            db.drop_all()

    def test_tracking_blocked_with_multiple_admins(self):
        """Test IP blocking works when multiple admins have different blocklists."""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:?check_same_thread=False"
        app.config["TESTING"] = True

        with app.app_context():
            db.create_all()

            # Create two admin users with different blocklists
            admin1 = AdminUser(
                email="multi1@test.com",
                oidc_sub="test-sub-multi1",
                roles=["admin"],
                ip_blocklist=["192.0.2.1"],
            )
            admin2 = AdminUser(
                email="multi2@test.com",
                oidc_sub="test-sub-multi2",
                roles=["admin"],
                ip_blocklist=["192.0.2.2"],
            )
            db.session.add(admin1)
            db.session.add(admin2)

            # Create recipient
            test_uuid = str(uuid.uuid4())
            recipient = Recipients(
                r_uuid=test_uuid, description="Test", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()

            with app.test_client() as client:
                # Request from IP in admin2's blocklist
                response = client.get(
                    f"/img/{test_uuid}",
                    headers={
                        "X-Forwarded-For": "192.0.2.2",
                        "User-Agent": "Mozilla/5.0 Test",
                    },
                    base_url="http://local.test",
                )
                assert response.status_code == 200

                # Verify tracking was blocked
                tracking_count = Tracking.query.count()
                assert tracking_count == 0

            db.session.remove()
            db.drop_all()

    def test_combined_filtering_cookie_and_ip(self):
        """Test that both cookie and IP filtering work together."""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:?check_same_thread=False"
        app.config["TESTING"] = True

        with app.app_context():
            db.create_all()

            # Create admin with IP blocklist (use unique email)
            admin = AdminUser(
                email="combined@test.com",
                oidc_sub="test-sub-combined",
                roles=["admin"],
                ip_blocklist=["198.51.100.1"],
            )
            db.session.add(admin)

            # Create recipient
            test_uuid = str(uuid.uuid4())
            recipient = Recipients(
                r_uuid=test_uuid, description="Test", email="test@example.com"
            )
            db.session.add(recipient)
            db.session.commit()

            with app.test_client() as client:
                # Test 1: Cookie present, IP NOT blocked - should skip tracking
                client.set_cookie("rr_ignore_me", "true", domain="local.test")
                response = client.get(
                    f"/img/{test_uuid}",
                    headers={"User-Agent": "Mozilla/5.0 Test"},
                    base_url="http://local.test",
                )
                assert response.status_code == 200

                tracking_count = Tracking.query.count()
                assert tracking_count == 0

                # Test 2: No cookie, IP blocked - should skip tracking
                client.set_cookie("rr_ignore_me", "", domain="local.test", max_age=0)
                response = client.get(
                    f"/img/{test_uuid}",
                    headers={
                        "X-Forwarded-For": "198.51.100.1",
                        "User-Agent": "Mozilla/5.0 Test",
                    },
                    base_url="http://local.test",
                )
                assert response.status_code == 200

                tracking_count = Tracking.query.count()
                assert tracking_count == 0  # Still 0

            db.session.remove()
            db.drop_all()


class TestAdminUserModel:
    """Tests for AdminUser model with ip_blocklist field."""

    def test_admin_user_has_ip_blocklist_field(self):
        """Test AdminUser model has ip_blocklist field."""
        app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:?check_same_thread=False"
        app.config["TESTING"] = True

        with app.app_context():
            db.create_all()

            admin = AdminUser(
                email="blocklist@test.com",
                oidc_sub="test-sub-blocklist",
                roles=["admin"],
                ip_blocklist=["192.168.1.1", "10.0.0.1"],
            )
            db.session.add(admin)
            db.session.commit()

            # Query and verify
            retrieved = AdminUser.query.filter_by(email="blocklist@test.com").first()
            assert retrieved is not None
            assert retrieved.ip_blocklist == ["192.168.1.1", "10.0.0.1"]

            db.session.remove()
            db.drop_all()

    def test_admin_user_to_dict_includes_blocklist(self):
        """Test AdminUser.to_dict includes ip_blocklist."""
        with app.app_context():
            admin = AdminUser(
                email="admin@test.com",
                oidc_sub="test-sub",
                roles=["admin"],
                ip_blocklist=["1.2.3.4"],
            )

            result = admin.to_dict()
            assert "ip_blocklist" in result
            assert result["ip_blocklist"] == ["1.2.3.4"]
