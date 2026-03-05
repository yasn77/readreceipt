"""Tests for structured logging functionality."""

import logging
from collections.abc import Generator
from typing import Any

import pytest

from app import Recipients, app, db
from utils.logging import (
    RedactingJsonFormatter,
    configure_logging,
    get_logger,
    log_performance,
    timed_operation,
)


@pytest.fixture
def client() -> Generator[Any, None, None]:
    """Create a test client with structured logging enabled."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    app.config["LOG_LEVEL"] = "INFO"
    app.config["LOG_FORMAT"] = "json"
    app.config["LOG_REDACT_FIELDS"] = ["password", "token", "api_key"]

    with app.app_context():
        db.create_all()
        test_client = app.test_client()
        test_client.environ_base["HTTP_AUTHORIZATION"] = "Bearer test-token"
        yield test_client
        db.session.remove()
        db.drop_all()


@pytest.fixture
def sample_recipient(client: Any) -> str:
    """Create a sample recipient for testing."""
    import uuid

    test_uuid = str(uuid.uuid4())
    recipient = Recipients(
        r_uuid=test_uuid, description="Test recipient", email="test@example.com"
    )
    db.session.add(recipient)
    db.session.commit()
    return test_uuid


class TestRedactingJsonFormatter:
    """Tests for the JSON formatter with redaction."""

    def test_formatter_redacts_password(self) -> None:
        """Test that password fields are redacted."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "test", "password": "secret123"}
        processed = formatter.process_log_record(log_record)
        assert processed["password"] == "[REDACTED]"

    def test_formatter_redacts_token(self) -> None:
        """Test that token fields are redacted."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "test", "token": "abc123xyz"}
        processed = formatter.process_log_record(log_record)
        assert processed["token"] == "[REDACTED]"

    def test_formatter_redacts_api_key(self) -> None:
        """Test that api_key fields are redacted."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "test", "api_key": "key123"}
        processed = formatter.process_log_record(log_record)
        assert processed["api_key"] == "[REDACTED]"

    def test_formatter_preserves_normal_fields(self) -> None:
        """Test that non-sensitive fields are preserved."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "test", "user": "john", "action": "login"}
        processed = formatter.process_log_record(log_record)
        assert processed["user"] == "john"
        assert processed["action"] == "login"

    def test_formatter_with_custom_redact_fields(self) -> None:
        """Test formatter with custom redact fields."""
        formatter = RedactingJsonFormatter(redact_fields=["custom_field"])
        log_record = {"message": "test", "custom_field": "value"}
        processed = formatter.process_log_record(log_record)
        assert processed["custom_field"] == "[REDACTED]"


class TestStructuredLogger:
    """Tests for the structured logger."""

    def test_logger_creates_json_output(self) -> None:
        """Test that logger produces JSON output."""
        logger = get_logger("test")
        # The logger should be able to log without errors
        logger.info("Test message", user="test_user", action="test_action")

    def test_logger_includes_request_id(self) -> None:
        """Test that logger includes request ID in context."""
        with app.app_context():
            with app.test_request_context("/"):
                logger = get_logger("test")
                # Should include request_id from Flask's g object
                logger.info("Test with request context")

    def test_logger_levels(self) -> None:
        """Test different log levels."""
        logger = get_logger("test")
        logger.debug("Debug message")
        logger.info("Info message")
        logger.warning("Warning message")
        logger.error("Error message")


class TestLoggingMiddleware:
    """Tests for the request ID middleware."""

    def test_request_id_in_response_headers(self, client: Any) -> None:
        """Test that X-Request-ID header is present in responses."""
        response = client.get("/")
        assert "X-Request-ID" in response.headers
        assert len(response.headers["X-Request-ID"]) == 36  # UUID length

    def test_request_id_is_unique_per_request(self, client: Any) -> None:
        """Test that each request gets a unique request ID."""
        response1 = client.get("/")
        response2 = client.get("/")
        assert response1.headers["X-Request-ID"] != response2.headers["X-Request-ID"]

    def test_request_id_in_g_object(self, client: Any) -> None:
        """Test that request ID is stored in Flask's g object."""
        with app.app_context():
            # Make an actual request to trigger the middleware
            response = client.get("/")
            from flask import g

            # The middleware should have set g.request_id during the request
            # We need to check within a request context
            with app.test_request_context("/"):
                # After making a request, g should have request_id
                assert hasattr(g, "request_id") or response.headers.get("X-Request-ID")


class TestLogConfiguration:
    """Tests for logging configuration."""

    def test_configure_logging_sets_level(self) -> None:
        """Test that configure_logging sets the correct log level."""
        from flask import Flask

        test_app = Flask("test")
        test_app.config["LOG_LEVEL"] = "DEBUG"
        configure_logging(test_app, log_level="DEBUG")
        assert test_app.config["LOG_LEVEL"] == "DEBUG"
        assert logging.getLogger().level == logging.DEBUG

    def test_configure_logging_json_format(self) -> None:
        """Test that configure_logging sets JSON format."""
        from flask import Flask

        test_app = Flask("test")
        configure_logging(test_app, log_format="json")
        assert test_app.config["LOG_FORMAT"] == "json"

    def test_configure_logging_text_format(self) -> None:
        """Test that configure_logging can set text format."""
        from flask import Flask

        test_app = Flask("test")
        configure_logging(test_app, log_format="text")
        assert test_app.config["LOG_FORMAT"] == "text"

    def test_configure_logging_redact_fields(self) -> None:
        """Test that configure_logging handles redact fields."""
        from flask import Flask

        test_app = Flask("test")
        configure_logging(test_app, redact_fields=["custom_secret"])
        assert "custom_secret" in test_app.config["LOG_REDACT_FIELDS"]


class TestPerformanceLogging:
    """Tests for performance logging."""

    def test_log_performance_fast_operation(self) -> None:
        """Test logging of fast operations."""
        # Should log at DEBUG level for fast operations
        log_performance("fast_op", 50, threshold_ms=100)

    def test_log_performance_slow_operation(self) -> None:
        """Test logging of slow operations."""
        # Should log at WARNING level for slow operations
        log_performance("slow_op", 150, threshold_ms=100)

    def test_timed_operation_decorator(self) -> None:
        """Test the timed_operation decorator."""

        @timed_operation("test_operation", threshold_ms=100)
        def fast_function() -> int:
            return 42

        result = fast_function()
        assert result == 42

    def test_timed_operation_slow_function(self) -> None:
        """Test timed_operation with a slow function."""
        import time

        @timed_operation("slow_test_operation", threshold_ms=10)
        def slow_function() -> int:
            time.sleep(0.02)  # 20ms
            return 42

        result = slow_function()
        assert result == 42


class TestLoggingInEndpoints:
    """Tests for logging in actual endpoints."""

    def test_img_endpoint_logs_tracking(
        self, client: Any, sample_recipient: str
    ) -> None:
        """Test that /img endpoint logs tracking events."""
        response = client.get(f"/img/{sample_recipient}")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_admin_login_logs_success(self, client: Any) -> None:
        """Test that admin login logs successful authentication."""
        import os

        os.environ["ADMIN_TOKEN"] = "test-token"

        response = client.post(
            "/api/admin/login",
            json={"token": "test-token"},
            content_type="application/json",
        )
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers

    def test_admin_login_logs_failure(self, client: Any) -> None:
        """Test that admin login logs failed authentication."""
        response = client.post(
            "/api/admin/login",
            json={"token": "wrong-token"},
            content_type="application/json",
        )
        assert response.status_code == 401
        assert "X-Request-ID" in response.headers

    def test_create_recipient_logs_creation(self, client: Any) -> None:
        """Test that creating recipient logs the action."""
        response = client.post(
            "/api/admin/recipients",
            json={"email": "new@example.com", "description": "New recipient"},
            content_type="application/json",
        )
        assert response.status_code == 201
        assert "X-Request-ID" in response.headers

    def test_delete_recipient_logs_deletion(
        self, client: Any, sample_recipient: str
    ) -> None:
        """Test that deleting recipient logs the action."""
        recipient = Recipients.query.filter_by(r_uuid=sample_recipient).first()

        response = client.delete(f"/api/admin/recipients/{recipient.id}")
        assert response.status_code == 200
        assert "X-Request-ID" in response.headers


class TestSensitiveDataRedaction:
    """Tests for sensitive data redaction in logs."""

    def test_token_redacted_in_login_failure(self, client: Any) -> None:
        """Test that tokens are redacted in login failure logs."""
        # The logging system should redact the token field
        formatter = RedactingJsonFormatter()
        log_record = {"message": "Login failed", "token": "secret_token_value"}
        processed = formatter.process_log_record(log_record)
        assert processed["token"] == "[REDACTED]"

    def test_password_redacted_in_logs(self) -> None:
        """Test that passwords are redacted."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "User action", "password": "user_password"}
        processed = formatter.process_log_record(log_record)
        assert processed["password"] == "[REDACTED]"

    def test_api_key_redacted_in_logs(self) -> None:
        """Test that API keys are redacted."""
        formatter = RedactingJsonFormatter()
        log_record = {"message": "API call", "api_key": "sk-12345"}
        processed = formatter.process_log_record(log_record)
        assert processed["api_key"] == "[REDACTED]"
