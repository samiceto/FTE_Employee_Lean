"""
Unit tests for retry handler decorator.
"""

import pytest
import time
from src.core.retry_handler import with_retry
from src.core.errors import TransientError


def test_retry_success_on_first_attempt():
    """Test successful execution on first attempt"""
    call_count = 0

    @with_retry(max_attempts=3)
    def succeeds_immediately():
        nonlocal call_count
        call_count += 1
        return "success"

    result = succeeds_immediately()
    assert result == "success"
    assert call_count == 1


def test_retry_success_on_second_attempt():
    """Test successful execution after retry"""
    call_count = 0

    @with_retry(max_attempts=3)
    def succeeds_on_retry():
        nonlocal call_count
        call_count += 1
        if call_count < 2:
            raise TransientError("Temporary failure")
        return "success"

    result = succeeds_on_retry()
    assert result == "success"
    assert call_count == 2


def test_retry_exhaustion():
    """Test retry exhaustion after max attempts"""
    call_count = 0

    @with_retry(max_attempts=3)
    def always_fails():
        nonlocal call_count
        call_count += 1
        raise TransientError("Always fails")

    with pytest.raises(TransientError):
        always_fails()

    assert call_count == 3


def test_exponential_backoff():
    """Test exponential backoff delays"""
    call_times = []

    @with_retry(max_attempts=3, base_delay=1, max_delay=10)
    def track_delays():
        call_times.append(time.time())
        raise TransientError("Test")

    start = time.time()
    with pytest.raises(TransientError):
        track_delays()
    elapsed = time.time() - start

    # Should have delays: 1s + 2s = 3s minimum
    assert elapsed >= 3
    assert len(call_times) == 3


def test_non_transient_error_no_retry():
    """Test that non-transient errors are not retried"""
    call_count = 0

    @with_retry(max_attempts=3)
    def raises_non_transient():
        nonlocal call_count
        call_count += 1
        raise ValueError("Not a transient error")

    with pytest.raises(ValueError):
        raises_non_transient()

    # Should only be called once (no retry)
    assert call_count == 1


def test_max_delay_cap():
    """Test that delay is capped at max_delay"""
    delays = []

    @with_retry(max_attempts=5, base_delay=10, max_delay=20)
    def track_max_delay():
        if delays:
            # Calculate actual delay
            actual_delay = time.time() - delays[-1]
            # Max delay should never exceed max_delay
            assert actual_delay <= 21  # Allow 1s tolerance
        delays.append(time.time())
        raise TransientError("Test")

    with pytest.raises(TransientError):
        track_max_delay()

    assert len(delays) == 5
