"""Structured JSON logging module for Read Receipt application.

This module provides JSON-formatted logging with request ID tracking,
sensitive data redaction, and performance monitoring capabilities.
"""

from __future__ import annotations

import json
import logging
import os
import re
import time
import uuid
from datetime import datetime, timezone
from functools import wraps
from typing import Any

from flask import Flask, g, request
from pythonjsonlogger import jsonlogger


class RedactingJsonFormatter(jsonlogger.JsonFormatter):
    """JSON formatter that redacts sensitive fields."""

    sensitive_fields: list[str] = [
        "password",
        "token",
        "api_key",
        "secret",
        "authorization",
        "cookie",
        "session_id",
        "credentials",
        "auth",
    ]

    def __init__(
        self,
        redact_fields: list[str] | None = None,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        """Initialise the formatter with optional custom redact fields.

        Args:
            redact_fields: Additional fields to redact beyond the defaults.
        """
        # Remove additional_fields from kwargs as it's not supported in newer versions
        kwargs.pop("additional_fields", None)
        super().__init__(*args, **kwargs)
        if redact_fields:
            self.sensitive_fields.extend(redact_fields)

    def _redact_value(self, value: Any) -> Any:
        """Redact sensitive values.

        Args:
            value: The value to potentially redact.

        Returns:
            The original value if not sensitive, or '[REDACTED]' if sensitive.
        """
        if isinstance(value, str):
            # Check if value looks like a token/key (long alphanumeric string)
            if len(value) > 8 and re.match(r"[a-zA-Z0-9_-]+", value):
                return "[REDACTED]"
        return value

    def process_log_record(self, log_record: dict[str, Any]) -> dict[str, Any]:
        """Process and redact sensitive fields from log record.

        Args:
            log_record: The log record dictionary.

        Returns:
            The processed log record with sensitive fields redacted.
        """
        for key in list(log_record.keys()):
            # Check if key contains sensitive patterns
            for sensitive_field in self.sensitive_fields:
                if sensitive_field in key.lower():
                    log_record[key] = "[REDACTED]"
                    break

            # Redact values that look like tokens
            if key.lower() in self.sensitive_fields:
                log_record[key] = self._redact_value(log_record[key])

        return log_record


def get_request_id() -> str:
    """Get or generate a request ID for the current request.

    Returns:
        A UUID string representing the request ID.
    """
    try:
        if not hasattr(g, "request_id"):
            g.request_id = str(uuid.uuid4())
        return g.request_id
    except RuntimeError:
        # Outside of request context, generate a new ID
        return str(uuid.uuid4())


def get_log_context() -> dict[str, Any]:
    """Build standard log context for current request.

    Returns:
        Dictionary containing standard logging fields.
    """
    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "request_id": get_request_id(),
        "logging_module": __name__,
        "logging_function": None,  # Will be set by logger
    }


def configure_logging(
    app: Flask,
    log_level: str | None = None,
    log_format: str | None = None,
    redact_fields: list[str] | None = None,
) -> None:
    """Configure application logging.

    Args:
        app: The Flask application instance.
        log_level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
        log_format: 'json' or 'text'. Defaults to 'json'.
        redact_fields: Additional fields to redact from logs.
    """
    # Get configuration from environment or defaults
    level = log_level or os.environ.get("LOG_LEVEL", "INFO")
    format_type = log_format or os.environ.get("LOG_FORMAT", "json")

    # Get redact fields from config or environment
    redact_list = redact_fields or os.environ.get("LOG_REDACT_FIELDS", "").split(",")
    redact_list = [f.strip() for f in redact_list if f.strip()]

    # Create logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers = []

    # Create handler
    handler = logging.StreamHandler()
    handler.setLevel(getattr(logging, level.upper()))

    if format_type == "json":
        # JSON formatter with redaction
        formatter = RedactingJsonFormatter(
            redact_fields=redact_list,
            additional_fields=[
                "timestamp",
                "level",
                "logging_module",
                "logging_function",
                "request_id",
                "user",
                "action",
                "result",
                "duration_ms",
            ],
        )
    else:
        # Text formatter for development
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Store configuration in app config
    app.config["LOG_LEVEL"] = level
    app.config["LOG_FORMAT"] = format_type
    app.config["LOG_REDACT_FIELDS"] = redact_list


class StructuredLogger:
    """Structured logger wrapper for consistent logging."""

    def __init__(self, name: str) -> None:
        """Initialise the structured logger.

        Args:
            name: The logger name.
        """
        self.logger = logging.getLogger(name)

    def _log(
        self,
        level: str,
        message: str,
        **kwargs: Any,
    ) -> None:
        """Log a message with structured context.

        Args:
            level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
            message: The log message.
            **kwargs: Additional context fields.
        """
        context = get_log_context()
        context.update(kwargs)
        context["message"] = message
        context["level"] = level

        # Filter out reserved LogRecord attributes to avoid conflicts
        reserved_attrs = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "taskName",
            "asctime",
            "message",  # Also exclude message as it's set by the logging system
        }
        filtered_context = {k: v for k, v in context.items() if k not in reserved_attrs}

        log_method = getattr(self.logger, level.lower())
        # Pass context as extra fields for the formatter to handle
        log_method(message, extra=filtered_context)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log a debug message."""
        self._log("DEBUG", message, **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log an info message."""
        self._log("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log a warning message."""
        self._log("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log an error message."""
        self._log("ERROR", message, **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log a critical message."""
        self._log("CRITICAL", message, **kwargs)


def get_logger(name: str) -> StructuredLogger:
    """Get a structured logger instance.

    Args:
        name: The logger name.

    Returns:
        A StructuredLogger instance.
    """
    return StructuredLogger(name)


def log_request_start() -> str:
    """Log the start of a request and return the request ID.

    Returns:
        The request ID.
    """
    request_id = get_request_id()
    logger = get_logger("request")
    logger.info(
        "Request started",
        path=request.path,
        method=request.method,
        user_agent=request.headers.get("User-Agent", ""),
    )
    return request_id


def log_request_end(
    status_code: int,
    duration_ms: float | None = None,
) -> None:
    """Log the end of a request.

    Args:
        status_code: The HTTP status code.
        duration_ms: Request duration in milliseconds.
    """
    logger = get_logger("request")
    logger.info(
        "Request completed",
        status_code=status_code,
        duration_ms=duration_ms,
        path=request.path,
    )


def log_performance(
    operation: str,
    duration_ms: float,
    threshold_ms: float = 100,
    **kwargs: Any,
) -> None:
    """Log performance metrics for slow operations.

    Args:
        operation: The operation name.
        duration_ms: Duration in milliseconds.
        threshold_ms: Threshold for marking as slow.
        **kwargs: Additional context.
    """
    logger = get_logger("performance")

    if duration_ms > threshold_ms:
        logger.warning(
            "Slow operation detected",
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
            **kwargs,
        )
    else:
        logger.debug(
            "Operation completed",
            operation=operation,
            duration_ms=duration_ms,
            **kwargs,
        )


def timed_operation(
    operation_name: str,
    threshold_ms: float = 100,
) -> Any:
    """Decorator to log timing for operations.

    Args:
        operation_name: Name of the operation for logging.
        threshold_ms: Threshold for marking as slow.

    Returns:
        Decorated function.
    """

    def decorator(func: Any) -> Any:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            duration_ms = (time.perf_counter() - start_time) * 1000

            log_performance(
                operation_name,
                duration_ms,
                threshold_ms,
                function=func.__name__,
            )

            return result

        return wrapper

    return decorator


class RequestIDMiddleware:
    """Middleware to inject request ID into all requests."""

    def __init__(self, app: Flask) -> None:
        """Initialise the middleware.

        Args:
            app: The Flask application.
        """
        self.app = app

    def before_request(self) -> None:
        """Generate request ID before each request."""
        g.request_id = str(uuid.uuid4())
        g.request_start_time = time.perf_counter()

    def after_request(self, response: Any) -> Any:
        """Add request ID to response headers and log completion."""
        # Add request ID to response headers
        response.headers["X-Request-ID"] = g.request_id

        # Calculate duration
        if hasattr(g, "request_start_time"):
            duration_ms = (time.perf_counter() - g.request_start_time) * 1000
            try:
                log_request_end(response.status_code, duration_ms)
            except Exception:
                # Silently ignore logging errors to prevent breaking the application
                pass

        return response


def init_logging_middleware(app: Flask) -> None:
    """Initialise logging middleware on the application.

    Args:
        app: The Flask application.
    """
    middleware = RequestIDMiddleware(app)
    app.before_request(middleware.before_request)
    app.after_request(middleware.after_request)
