"""
Retry handler decorator with exponential backoff.

Provides a decorator for automatic retry of operations that fail with transient errors.
"""

import time
import logging
from functools import wraps
from .errors import TransientError

logger = logging.getLogger(__name__)


def with_retry(max_attempts=3, base_delay=1, max_delay=60):
    """
    Retry decorator with exponential backoff.

    Only retries operations that fail with TransientError exceptions.
    All other exceptions are raised immediately.

    Args:
        max_attempts: Maximum retry attempts (default: 3)
        base_delay: Initial delay in seconds (default: 1)
        max_delay: Maximum delay in seconds (default: 60)

    Usage:
        @with_retry(max_attempts=3, base_delay=1, max_delay=60)
        def risky_operation():
            # Operation that may fail transiently
            pass

    Returns:
        Decorator function that wraps the target function with retry logic.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_attempts):
                try:
                    return func(*args, **kwargs)
                except TransientError as e:
                    if attempt == max_attempts - 1:
                        logger.error(
                            f'{func.__name__} failed after {max_attempts} attempts: {e}'
                        )
                        raise

                    delay = min(base_delay * (2 ** attempt), max_delay)
                    logger.warning(
                        f'{func.__name__} attempt {attempt + 1}/{max_attempts} failed: {e}. '
                        f'Retrying in {delay}s...'
                    )
                    time.sleep(delay)

        return wrapper
    return decorator
