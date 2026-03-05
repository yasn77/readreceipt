"""
Retry logic with exponential backoff for database operations.

This module provides a decorator for retrying operations that may fail transiently,
such as database commits. It uses exponential backoff with jitter to prevent
thundering herd problems.
"""

from __future__ import annotations

import logging
import random
from functools import wraps
from typing import Any, Callable, TypeVar

from tenacity import (
    after_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential_jitter,
)

logger = logging.getLogger(__name__)

# Type variable for generic function signatures
F = TypeVar("F", bound=Callable[..., Any])


def get_retry_config(app_config: dict[str, Any] | None = None) -> dict[str, Any]:
    """
    Get retry configuration from app config or use defaults.

    Args:
        app_config: Flask application configuration dictionary.

    Returns:
        Dictionary with retry configuration values.
    """
    if app_config is None:
        app_config = {}

    return {
        "max_attempts": app_config.get("RETRY_MAX_ATTEMPTS", 5),
        "base_delay": app_config.get("RETRY_BASE_DELAY", 2),
        "max_delay": app_config.get("RETRY_MAX_DELAY", 30),
        "jitter": app_config.get("RETRY_JITTER", True),
    }


def create_retry_decorator(
    max_attempts: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
    logger_obj: logging.Logger | None = None,
) -> Callable[[F], F]:
    """
    Create a retry decorator with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts (default: 5).
        base_delay: Base delay in seconds for exponential backoff (default: 2).
        max_delay: Maximum delay between retries in seconds (default: 30).
        jitter: Whether to add random jitter to prevent thundering herd (default: True).
        exceptions: Tuple of exception types to retry on (default: all Exceptions).
        logger_obj: Logger instance for logging retry attempts (default: module logger).

    Returns:
        A decorator function that can be applied to other functions.
    """
    if logger_obj is None:
        logger_obj = logger

    wait_strategy = wait_exponential_jitter(
        initial=base_delay,
        max=max_delay,
        exp_base=2,
        jitter=1.0 if jitter else 0.0,
    )

    retry_strategy = retry(
        retry=retry_if_exception_type(exceptions),
        wait=wait_strategy,
        stop=stop_after_attempt(max_attempts),
        after=after_log(logger_obj, logging.WARNING),
        reraise=True,
    )

    def decorator(func: F) -> F:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            return retry_strategy(func)(*args, **kwargs)

        return wrapper  # type: ignore[return-value]

    return decorator


def retry_with_backoff(
    func: Callable[..., Any] | None = None,
    *,
    max_attempts: int = 5,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
    exceptions: tuple[type[Exception], ...] = (Exception,),
) -> Callable[..., Any]:
    """
    Decorator for retrying functions with exponential backoff.

    Can be used with or without parameters:
        @retry_with_backoff
        def my_func(): ...

        @retry_with_backoff(max_attempts=3, base_delay=1.0)
        def my_func(): ...

    Args:
        func: The function to decorate (when used without parentheses).
        max_attempts: Maximum number of retry attempts (default: 5).
        base_delay: Base delay in seconds for exponential backoff (default: 2).
        max_delay: Maximum delay between retries in seconds (default: 30).
        jitter: Whether to add random jitter (default: True).
        exceptions: Tuple of exception types to retry on (default: all Exceptions).

    Returns:
        Decorated function with retry logic.

    Example:
        >>> @retry_with_backoff(max_attempts=3)
        ... def database_commit():
        ...     db.session.commit()
    """
    if func is None:
        # Called with parameters
        def decorator(f: Callable[..., Any]) -> Callable[..., Any]:
            return create_retry_decorator(
                max_attempts=max_attempts,
                base_delay=base_delay,
                max_delay=max_delay,
                jitter=jitter,
                exceptions=exceptions,
            )(f)

        return decorator

    # Called without parameters
    return create_retry_decorator(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        jitter=jitter,
        exceptions=exceptions,
    )(func)


def calculate_backoff_delay(
    attempt: int,
    base_delay: float = 2.0,
    max_delay: float = 30.0,
    jitter: bool = True,
) -> float:
    """
    Calculate the delay for a given retry attempt.

    Args:
        attempt: The current attempt number (1-indexed).
        base_delay: Base delay in seconds.
        max_delay: Maximum delay in seconds.
        jitter: Whether to add random jitter.

    Returns:
        Delay in seconds for this attempt.
    """
    # Exponential backoff: base_delay * 2^(attempt - 1)
    delay = base_delay * (2 ** (attempt - 1))

    # Cap at max_delay
    delay = min(delay, max_delay)

    # Add jitter (±25% of delay)
    if jitter:
        jitter_range = delay * 0.25
        delay += random.uniform(-jitter_range, jitter_range)

    return max(0, delay)
