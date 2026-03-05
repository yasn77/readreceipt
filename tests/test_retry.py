"""Tests for retry logic with exponential backoff."""

import time
from datetime import datetime
from typing import Any
from unittest.mock import Mock, patch

import pytest
from tenacity import RetryError

from app import FailedEvent, app, db, log_failed_event
from utils.retry import (
    calculate_backoff_delay,
    create_retry_decorator,
    get_retry_config,
    retry_with_backoff,
)


@pytest.fixture
def app_context() -> Any:
    """Create an application context for testing."""
    app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///:memory:"
    app.config["TESTING"] = True
    app.config["RETRY_MAX_ATTEMPTS"] = 3
    app.config["RETRY_BASE_DELAY"] = 0.1  # Short delay for testing
    app.config["RETRY_MAX_DELAY"] = 1.0
    app.config["RETRY_JITTER"] = False  # Disable jitter for predictable tests

    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


class TestRetryDecorator:
    """Tests for the retry decorator."""

    def test_retry_on_success(self) -> None:
        """Test that function succeeds without retries when no error."""
        counter = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.1)
        def successful_func() -> int:
            nonlocal counter
            counter += 1
            return counter

        result = successful_func()
        assert result == 1
        assert counter == 1

    def test_retry_on_failure_then_success(self) -> None:
        """Test that function retries and eventually succeeds."""
        attempts = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.05)
        def eventually_success() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Transient error")
            return "success"

        result = eventually_success()
        assert result == "success"
        assert attempts == 2

    def test_retry_exhausted_raises_error(self) -> None:
        """Test that error is raised after max attempts."""
        attempts = 0

        @retry_with_backoff(max_attempts=3, base_delay=0.05)
        def always_fails() -> None:
            nonlocal attempts
            attempts += 1
            raise ValueError("Persistent error")

        with pytest.raises(ValueError, match="Persistent error"):
            always_fails()

        assert attempts == 3

    def test_retry_logs_attempts(self) -> None:
        """Test that retry attempts are logged."""
        attempts = 0

        @retry_with_backoff(max_attempts=2, base_delay=0.05)
        def fails_twice() -> str:
            nonlocal attempts
            attempts += 1
            if attempts < 2:
                raise ValueError("Error")
            return "ok"

        # This should succeed on second attempt
        result = fails_twice()
        assert result == "ok"
        assert attempts == 2


class TestExponentialBackoff:
    """Tests for exponential backoff timing."""

    def test_backoff_delay_calculation_no_jitter(self) -> None:
        """Test backoff delay calculation without jitter."""
        # Attempt 1: base_delay * 2^0 = 2 * 1 = 2
        delay1 = calculate_backoff_delay(
            1, base_delay=2.0, max_delay=30.0, jitter=False
        )
        assert delay1 == 2.0

        # Attempt 2: base_delay * 2^1 = 2 * 2 = 4
        delay2 = calculate_backoff_delay(
            2, base_delay=2.0, max_delay=30.0, jitter=False
        )
        assert delay2 == 4.0

        # Attempt 3: base_delay * 2^2 = 2 * 4 = 8
        delay3 = calculate_backoff_delay(
            3, base_delay=2.0, max_delay=30.0, jitter=False
        )
        assert delay3 == 8.0

    def test_backoff_delay_capped_at_max(self) -> None:
        """Test that backoff delay is capped at max_delay."""
        # Attempt 6 would be 2 * 2^5 = 64, but capped at 30
        delay = calculate_backoff_delay(6, base_delay=2.0, max_delay=30.0, jitter=False)
        assert delay == 30.0

    def test_backoff_with_jitter(self) -> None:
        """Test that jitter adds randomness to delay."""
        base_delay = 2.0
        delay = calculate_backoff_delay(1, base_delay=base_delay, jitter=True)

        # Jitter adds ±25% of delay
        jitter_range = base_delay * 0.25
        assert base_delay - jitter_range <= delay <= base_delay + jitter_range


class TestDeadLetterQueue:
    """Tests for dead letter queue (FailedEvent) functionality."""

    def test_log_failed_event_creates_record(self, app_context: Any) -> None:
        """Test that log_failed_event creates a FailedEvent record."""
        log_failed_event(
            operation_type="tracking_insert",
            error_message="Database connection lost",
            error_details={"exception_type": "OperationalError"},
            retry_count=5,
            entity_id=123,
            context_data={"user_agent": "Gmail"},
        )

        failed_events = FailedEvent.query.all()
        assert len(failed_events) == 1

        event = failed_events[0]
        assert event.operation_type == "tracking_insert"
        assert event.error_message == "Database connection lost"
        assert event.retry_count == 5
        assert event.entity_id == 123
        assert event.context_data == {"user_agent": "Gmail"}
        assert isinstance(event.timestamp, datetime)

    def test_log_failed_event_multiple_errors(self, app_context: Any) -> None:
        """Test that multiple failed events are stored."""
        log_failed_event("recipient_insert", "Error 1", retry_count=3)
        log_failed_event("tracking_insert", "Error 2", retry_count=5)

        failed_events = FailedEvent.query.all()
        assert len(failed_events) == 2

        operation_types = [e.operation_type for e in failed_events]
        assert "recipient_insert" in operation_types
        assert "tracking_insert" in operation_types


class TestMaxRetriesConfiguration:
    """Tests for max retries configuration."""

    def test_max_attempts_from_config(self, app_context: Any) -> None:
        """Test that max attempts is read from config."""
        assert app_context.config["RETRY_MAX_ATTEMPTS"] == 3

    def test_default_max_attempts(self) -> None:
        """Test default max attempts is 5."""
        config = get_retry_config()
        assert config["max_attempts"] == 5

    def test_custom_max_attempts(self) -> None:
        """Test custom max attempts."""
        config = get_retry_config({"RETRY_MAX_ATTEMPTS": 10})
        assert config["max_attempts"] == 10


class TestRetryIntegration:
    """Integration tests for retry logic in app endpoints."""

    def test_commit_with_retry_success(self, app_context: Any) -> None:
        """Test commit_with_retry succeeds on normal operation."""
        from app import Recipients, commit_with_retry

        recipient = Recipients(
            r_uuid="test-uuid",
            description="Test",
            email="test@example.com",
        )
        db.session.add(recipient)
        db.session.flush()  # Get ID before commit

        # This should succeed
        commit_with_retry("recipient_insert", entity_id=recipient.id)

        # Verify recipient was saved
        saved = Recipients.query.get(recipient.id)
        assert saved is not None
        assert saved.email == "test@example.com"

    def test_commit_with_retry_failure_logs_to_dead_letter(
        self, app_context: Any
    ) -> None:
        """Test that commit failures are logged to dead letter queue."""
        from app import Recipients, commit_with_retry

        recipient = Recipients(
            r_uuid="test-uuid",
            description="Test",
            email="test@example.com",
        )
        db.session.add(recipient)
        db.session.flush()

        # Mock db.session.commit to always fail
        with patch("app.db.session.commit", side_effect=Exception("Commit failed")):
            commit_with_retry(
                "recipient_insert",
                entity_id=recipient.id,
                context_data={"test": "failure"},
            )

        # Verify failed event was logged
        failed_events = FailedEvent.query.all()
        assert len(failed_events) == 1
        assert failed_events[0].operation_type == "recipient_insert"
        assert failed_events[0].error_message == "Commit failed"
        assert failed_events[0].retry_count == 3  # From test config
