"""
Error classification hierarchy for AI Employee autonomous system.

This module defines custom exception classes for different types of errors,
each with specific recovery strategies:
- Transient → Exponential backoff retry (auto-recover)
- Authentication → Alert human, pause operations
- Logic → Human review queue
- Data → Quarantine + alert
- System → Watchdog restart
"""


class TransientError(Exception):
    """
    Errors that may resolve on retry (network, rate limits, timeouts).

    Recovery: Exponential backoff retry with max attempts.
    """
    pass


class NetworkTimeout(TransientError):
    """Network operation timed out."""
    pass


class RateLimitExceeded(TransientError):
    """API rate limit exceeded."""
    pass


class ServiceUnavailable(TransientError):
    """External service temporarily unavailable."""
    pass


class AuthenticationError(Exception):
    """
    Authentication/authorization failures requiring human intervention.

    Recovery: Alert human, pause operations.
    """
    pass


class TokenExpired(AuthenticationError):
    """Authentication token has expired."""
    pass


class InvalidCredentials(AuthenticationError):
    """Invalid credentials provided."""
    pass


class PermissionDenied(AuthenticationError):
    """Permission denied for requested operation."""
    pass


class LogicError(Exception):
    """
    Business logic errors requiring human review.

    Recovery: Send to human review queue.
    """
    pass


class TaskValidationError(LogicError):
    """Task failed validation checks."""
    pass


class PlanExecutionError(LogicError):
    """Error executing planned task."""
    pass


class DataError(Exception):
    """
    Data quality/corruption issues.

    Recovery: Quarantine data and alert.
    """
    pass


class CorruptedFile(DataError):
    """File is corrupted or unreadable."""
    pass


class MissingField(DataError):
    """Required field is missing from data."""
    pass


class ValidationError(DataError):
    """Data failed validation."""
    pass


class SystemError(Exception):
    """
    System-level failures (disk, memory, process crashes).

    Recovery: Watchdog restart.
    """
    pass


class ProcessCrashed(SystemError):
    """Process has crashed unexpectedly."""
    pass


class DiskFull(SystemError):
    """Disk space exhausted."""
    pass


class MemoryExhausted(SystemError):
    """Memory exhausted."""
    pass
