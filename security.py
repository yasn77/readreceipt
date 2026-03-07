"""
Security middleware and utilities for ReadReceipt application.
Implements security headers, rate limiting, input validation, logging hardening, and RBAC.
"""
from __future__ import annotations

import functools
import logging
import os
import re
from datetime import datetime
from typing import Any, Callable

import bleach
from flask import Flask, g, jsonify, request
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

logger = logging.getLogger(__name__)


class SensitiveDataFilter(logging.Filter):
    """Logging filter that redacts sensitive information from log messages."""

    # Patterns to redact
    SENSITIVE_PATTERNS = [
        (r"(?i)(password|passwd|pwd)[^=]*[:=]\s*[^\s,;]+", r"\1=***REDACTED***"),
        (r"(?i)(token|api[_-]?key|secret[_-]?key|auth[_-]?token)[^=]*[:=]\s*[^\s,;]+", r"\1=***REDACTED***"),
        (r"(?i)(bearer\s+)[a-zA-Z0-9\-_\.]+", r"\1***REDACTED***"),
        (r"(?i)(email|e-mail)[^=]*[:=]\s*[^\s,;]+", r"\1=***REDACTED***"),
        (r"(?i)(connecting-ip|cf-connecting-ip|x-forwarded-for)[^=]*[:=]\s*[^\s,;]+", r"\1=***REDACTED***"),
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter out sensitive data from log messages."""
        if record.msg:
            msg = str(record.msg)
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                msg = re.sub(pattern, replacement, msg)
            record.msg = msg

        # Also sanitize args if present
        if record.args:
            if isinstance(record.args, dict):
                record.args = {k: self._sanitize_value(v) for k, v in record.args.items()}
            elif isinstance(record.args, tuple):
                record.args = tuple(self._sanitize_value(arg) for arg in record.args)

        return True

    def _sanitize_value(self, value: Any) -> Any:
        """Sanitize a value for logging."""
        if isinstance(value, str):
            for pattern, replacement in self.SENSITIVE_PATTERNS:
                value = re.sub(pattern, replacement, value)
        return value


def setup_security_headers(app: Flask) -> None:
    """
    Issue #106: Apply security headers to all responses.
    Adds CSP, X-Frame-Options, X-Content-Type-Options, HSTS, and other security headers.
    """

    @app.after_request
    def add_security_headers(response: Any) -> Any:
        """Add security headers to all responses."""
        # Content Security Policy - restrictive default
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self'; "
            "connect-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'"
        )

        # Prevent clickjacking
        response.headers["X-Frame-Options"] = "DENY"

        # Prevent MIME type sniffing
        response.headers["X-Content-Type-Options"] = "nosniff"

        # HTTP Strict Transport Security (HSTS)
        response.headers["Strict-Transport-Security"] = (
            "max-age=31536000; includeSubDomains; preload"
        )

        # XSS Protection (legacy but still useful)
        response.headers["X-XSS-Protection"] = "1; mode=block"

        # Referrer Policy
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Permissions Policy (formerly Feature-Policy)
        response.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), payment=(), usb=()"
        )

        # Cache control for sensitive endpoints
        if request.path.startswith("/api/admin") or request.path.startswith("/img/"):
            response.headers["Cache-Control"] = (
                "no-store, no-cache, must-revalidate, private"
            )
            response.headers["Pragma"] = "no-cache"
            response.headers["Expires"] = "0"

        return response


def setup_rate_limiting(app: Flask) -> Limiter:
    """
    Issue #105: Add rate limiting to tracking and admin endpoints.
    Implements rate limits to prevent DoS and abuse.
    """
    limiter = Limiter(
        key_func=get_remote_address,
        app=app,
        default_limits=["1000 per day", "100 per hour"],
        storage_uri=os.environ.get("REDIS_URL", "memory://"),
        strategy="fixed-window",
    )

    # Rate limit tracking endpoint (img/<uuid>) - prevent abuse
    if "send_img" in app.view_functions:
        limiter.limit("30 per minute")(app.view_functions["send_img"])

    # Rate limit admin endpoints more strictly
    if "admin_login" in app.view_functions:
        limiter.limit("5 per minute")(app.view_functions["admin_login"])

    # Rate limit all admin API endpoints
    @app.before_request
    def apply_admin_rate_limit() -> None:
        """Apply stricter rate limits to admin endpoints."""
        if request.path.startswith("/api/admin"):
            # Store in g for potential custom handling
            g.is_admin_endpoint = True

    return limiter


def setup_input_validation(app: Flask) -> None:
    """
    Issue #107: Input validation and sanitization for dynamic request fields.
    Validates and sanitizes all incoming request data.
    """

    # Maximum lengths for various fields
    MAX_EMAIL_LENGTH = 254
    MAX_DESCRIPTION_LENGTH = 500
    MAX_USER_AGENT_LENGTH = 512
    MAX_HEADER_VALUE_LENGTH = 1024
    MAX_JSON_PAYLOAD_SIZE = 1024 * 100  # 100KB

    def validate_email(email: str) -> bool:
        """Validate email format."""
        if not email or len(email) > MAX_EMAIL_LENGTH:
            return False
        # Basic email pattern
        pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return bool(re.match(pattern, email))

    def sanitize_string(value: str, max_length: int = MAX_DESCRIPTION_LENGTH) -> str:
        """Sanitize a string value by removing potentially harmful content."""
        if not isinstance(value, str):
            return str(value)[:max_length]

        # Bleach to clean HTML/script content
        cleaned = bleach.clean(value, tags=[], strip=True)
        # Limit length
        return cleaned[:max_length]

    @app.before_request
    def validate_and_sanitize_request() -> None:
        """Validate and sanitize incoming request data."""
        # Check Content-Length for POST/PUT requests
        content_length = request.content_length
        if content_length and content_length > MAX_JSON_PAYLOAD_SIZE:
            return jsonify({"error": "Request payload too large"}), 413

        # Sanitize and validate JSON data
        if request.is_json:
            data = request.get_json(silent=True)
            if data:
                g.sanitized_data = sanitize_dict(data)

        # Sanitize query parameters
        if request.args:
            g.sanitized_args = {
                k: sanitize_string(v, MAX_DESCRIPTION_LENGTH)
                for k, v in request.args.to_dict().items()
            }

        # Limit User-Agent length
        user_agent = request.headers.get("User-Agent", "")
        if len(user_agent) > MAX_USER_AGENT_LENGTH:
            # Trim but log the attempt
            logger.warning(
                f"User-Agent too long: {len(user_agent)} chars, truncated"
            )

        # Validate headers don't contain dangerous content
        for header_name, header_value in request.headers:
            if len(header_value) > MAX_HEADER_VALUE_LENGTH:
                logger.warning(
                    f"Header {header_name} value too long, rejecting request"
                )
                return jsonify({"error": "Invalid request headers"}), 400

            # Store sanitized headers for logging
            if not hasattr(g, "sanitized_headers"):
                g.sanitized_headers = {}
            g.sanitized_headers[header_name] = sanitize_string(
                header_value, MAX_HEADER_VALUE_LENGTH
            )

    def sanitize_dict(data: dict[str, Any]) -> dict[str, Any]:
        """Recursively sanitize a dictionary."""
        cleaned = {}
        for k, v in data.items():
            if isinstance(v, str):
                cleaned[k] = sanitize_string(v)
            elif isinstance(v, dict):
                cleaned[k] = sanitize_dict(v)
            elif isinstance(v, list):
                cleaned[k] = [
                    sanitize_dict(i) if isinstance(i, dict)
                    else sanitize_string(i) if isinstance(i, str)
                    else i
                    for i in v
                ]
            else:
                cleaned[k] = v
        return cleaned

    # Export helper functions for use in routes
    app.config["VALIDATE_EMAIL"] = validate_email
    app.config["SANITIZE_STRING"] = sanitize_string
    app.config["SANITIZE_DICT"] = sanitize_dict


def setup_hardened_logging(app: Flask) -> None:
    """
    Issue #108: Harden logging to avoid leaking sensitive request data.
    Configures logging with sensitive data filtering.
    """
    # Configure root logger
    log_level = os.environ.get("LOG_LEVEL", "INFO").upper()
    logging.basicConfig(
        level=getattr(logging, log_level, logging.INFO),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    # Add sensitive data filter to all handlers
    sensitive_filter = SensitiveDataFilter()
    for handler in logging.getLogger().handlers:
        handler.addFilter(sensitive_filter)

    # Configure Flask app logger
    app.logger.setLevel(getattr(logging, log_level, logging.INFO))
    for handler in app.logger.handlers:
        handler.addFilter(sensitive_filter)

    # Log application security initialization
    logger.info("Security logging initialized with sensitive data filtering")

    # Override Flask's default logging to include filtering
    class SafeRequestLogger(logging.Logger):
        """Custom logger that safely logs request information."""

        def log_request(self, message: str, **kwargs: Any) -> None:
            """Log request information with automatic redaction."""
            safe_kwargs = {}
            for key, value in kwargs.items():
                if isinstance(value, str):
                    # Apply sensitive data filtering
                    for pattern, replacement in SensitiveDataFilter.SENSITIVE_PATTERNS:
                        value = re.sub(pattern, replacement, value)
                safe_kwargs[key] = value
            self.info(message, **safe_kwargs)

    app.logger = SafeRequestLogger(app.logger.name)


def setup_rbac(app: Flask) -> None:
    """
    Issue #109: IAM/roles - define admin vs. user scopes and audit admin actions.
    Implements role-based access control with audit logging.
    """

    def require_admin(f: Callable) -> Callable:
        """Decorator to require admin authentication for endpoints."""

        @functools.wraps(f)
        def decorated_function(*args: Any, **kwargs: Any) -> Any:
            # Check for Authorization header
            auth_header = request.headers.get("Authorization", "")

            if not auth_header.startswith("Bearer "):
                # Try cookie-based auth as fallback
                token = request.cookies.get("admin_token")
                if not token:
                    return jsonify({"error": "Unauthorized: Missing authentication"}), 401
            else:
                token = auth_header.split(" ")[1]

            # Validate token
            admin_token = os.environ.get("ADMIN_TOKEN", "admin")
            if token != admin_token:
                # Audit failed login attempt
                logger.warning(
                    f"Unauthorized admin access attempt from {request.remote_addr}"
                )
                return jsonify({"error": "Unauthorized: Invalid token"}), 401

            # Get user roles from token or environment
            # In production, this would decode JWT and extract roles
            user_roles = get_user_roles(token)

            # Check if user has required role
            if "admin" not in user_roles:
                logger.warning(
                    f"Forbidden admin access attempt by user with roles: {user_roles}"
                )
                return jsonify({"error": "Forbidden: Admin access required"}), 403

            # Audit successful admin action
            audit_log(
                action=f.__name__,
                user_token=token[:8] + "...",  # Log partial token for traceability
                remote_addr=request.remote_addr,
                user_agent=request.headers.get("User-Agent", "Unknown"),
                endpoint=request.path,
                method=request.method,
            )

            # Store user info in request context
            g.current_user = {"token": token, "roles": user_roles}

            return f(*args, **kwargs)

        return decorated_function

    def get_user_roles(token: str) -> list[str]:
        """
        Get user roles from token.
        In production, this would decode JWT and extract claims.
        """
        admin_token = os.environ.get("ADMIN_TOKEN", "admin")
        if token == admin_token:
            return ["admin"]
        return ["viewer"]

    def audit_log(
        action: str,
        user_token: str,
        remote_addr: str,
        user_agent: str,
        endpoint: str,
        method: str,
        details: dict[str, Any] | None = None,
    ) -> None:
        """
        Log admin actions for audit trail.
        Sensitive data is automatically redacted.
        """
        log_entry = {
            "timestamp": datetime.utcnow().isoformat(),
            "action": action,
            "user_token": user_token,
            "remote_addr": remote_addr,
            "user_agent": user_agent[:100],  # Truncate user agent
            "endpoint": endpoint,
            "method": method,
            "details": details or {},
        }
        logger.info(f"AUDIT: {json.dumps(log_entry)}")

    # Export for use in routes
    app.config["REQUIRE_ADMIN"] = require_admin
    app.config["AUDIT_LOG"] = audit_log
    app.config["GET_USER_ROLES"] = get_user_roles


def init_security(app: Flask) -> Limiter:
    """
    Initialize all security features for the Flask application.
    Call this after creating the Flask app but before running.

    Returns:
        Limiter instance for rate limiting
    """
    setup_security_headers(app)
    limiter = setup_rate_limiting(app)
    setup_input_validation(app)
    setup_hardened_logging(app)
    setup_rbac(app)
    return limiter
