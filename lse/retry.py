"""Retry logic with exponential backoff for LangSmith API operations."""

import logging
import random
import time
from functools import wraps
from typing import Any, Callable, Optional, Type

from lse.exceptions import APIError

logger = logging.getLogger(__name__)


class RetryConfig:
    """Configuration for retry operations."""

    def __init__(
        self,
        max_attempts: int = 5,
        base_delay: float = 1.0,
        max_delay: float = 60.0,
        backoff_multiplier: float = 2.0,
        jitter: bool = True,
    ):
        """Initialize retry configuration.

        Args:
            max_attempts: Maximum number of retry attempts
            base_delay: Initial delay between retries in seconds
            max_delay: Maximum delay between retries in seconds
            backoff_multiplier: Factor to multiply delay by for each retry
            jitter: Whether to add random jitter to delay
        """
        self.max_attempts = max_attempts
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.backoff_multiplier = backoff_multiplier
        self.jitter = jitter

    def calculate_delay(self, attempt: int) -> float:
        """Calculate delay for a given attempt number.

        Args:
            attempt: The attempt number (0-based)

        Returns:
            Delay in seconds
        """
        delay = self.base_delay * (self.backoff_multiplier**attempt)
        delay = min(delay, self.max_delay)

        if self.jitter:
            # Add random jitter (±25%)
            jitter_amount = delay * 0.25
            delay += random.uniform(-jitter_amount, jitter_amount)
            delay = max(0, delay)  # Ensure non-negative

        return delay


def is_retryable_error(error: Exception) -> bool:
    """Determine if an error should trigger a retry.

    Args:
        error: The exception that occurred

    Returns:
        True if the error is transient and should be retried
    """
    if isinstance(error, APIError):
        # Check the underlying error message for specific HTTP status codes
        error_msg = str(error).lower()

        # Retryable HTTP errors
        retryable_patterns = [
            "429",  # Too Many Requests (rate limiting)
            "500",  # Internal Server Error
            "502",  # Bad Gateway
            "503",  # Service Unavailable
            "504",  # Gateway Timeout
            "timeout",  # General timeout errors
            "connection",  # Connection errors
            "network",  # Network errors
        ]

        return any(pattern in error_msg for pattern in retryable_patterns)

    # Check for other transient errors
    if isinstance(error, (ConnectionError, TimeoutError)):
        return True

    # Don't retry authentication errors, validation errors, etc.
    return False


def with_retry(
    config: Optional[RetryConfig] = None,
    retryable_exceptions: Optional[tuple[Type[Exception], ...]] = None,
) -> Callable:
    """Decorator to add retry logic to functions.

    Args:
        config: Retry configuration (uses default if not provided)
        retryable_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    if config is None:
        config = RetryConfig()

    if retryable_exceptions is None:
        retryable_exceptions = (APIError, ConnectionError, TimeoutError)

    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(config.max_attempts):
                try:
                    return func(*args, **kwargs)

                except retryable_exceptions as e:
                    last_exception = e

                    # Check if this specific error should be retried
                    if not is_retryable_error(e):
                        logger.debug(f"Error is not retryable: {e}")
                        raise

                    # Don't sleep on the last attempt
                    if attempt < config.max_attempts - 1:
                        delay = config.calculate_delay(attempt)
                        logger.warning(
                            f"Attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                            f"Retrying in {delay:.2f} seconds..."
                        )
                        time.sleep(delay)
                    else:
                        logger.error(f"All {config.max_attempts} attempts failed. Last error: {e}")

                except Exception as e:
                    # Non-retryable exception, fail immediately
                    logger.debug(f"Non-retryable error: {e}")
                    raise

            # If we get here, all retries were exhausted
            raise last_exception

        return wrapper

    return decorator


def retry_operation(
    operation: Callable,
    config: Optional[RetryConfig] = None,
    operation_name: Optional[str] = None,
) -> Any:
    """Retry an operation with exponential backoff.

    Args:
        operation: Function to retry
        config: Retry configuration
        operation_name: Name for logging purposes

    Returns:
        Result of the operation

    Raises:
        Exception: The last exception after all retries are exhausted
    """
    if config is None:
        config = RetryConfig()

    op_name = operation_name or getattr(operation, "__name__", "operation")
    last_exception = None

    for attempt in range(config.max_attempts):
        try:
            logger.debug(f"Attempting {op_name} (attempt {attempt + 1}/{config.max_attempts})")
            return operation()

        except Exception as e:
            last_exception = e

            # Check if this error should be retried
            if not is_retryable_error(e):
                logger.debug(f"{op_name} failed with non-retryable error: {e}")
                raise

            # Don't sleep on the last attempt
            if attempt < config.max_attempts - 1:
                delay = config.calculate_delay(attempt)
                logger.warning(
                    f"{op_name} attempt {attempt + 1}/{config.max_attempts} failed: {e}. "
                    f"Retrying in {delay:.2f} seconds..."
                )
                time.sleep(delay)
            else:
                logger.error(
                    f"{op_name} failed after {config.max_attempts} attempts. Last error: {e}"
                )

    # If we get here, all retries were exhausted
    raise last_exception
