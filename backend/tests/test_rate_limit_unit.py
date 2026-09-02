"""Unit tests for the in-process rate limiter.

Covers the time-window, status inspection, and GC behavior in isolation from HTTP routing.
"""

import time
import pytest
from fastapi import HTTPException
from app.security.rate_limit import (
    InMemoryRateLimiter,
    RateLimitConfig,
    check_rate_limit,
    get_rate_limit_status,
)


def test_under_limit_allows():
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=3, window_seconds=60)
    for _ in range(3):
        ok, _retry = limiter.check("user-1", cfg)
        assert ok is True


def test_at_limit_blocks():
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=2, window_seconds=60)
    assert limiter.check("user-1", cfg)[0] is True
    assert limiter.check("user-1", cfg)[0] is True
    ok, retry = limiter.check("user-1", cfg)
    assert ok is False
    assert retry is not None
    assert 0 < retry <= 60


def test_separate_users_have_separate_buckets():
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=1, window_seconds=60)
    assert limiter.check("alice", cfg)[0] is True
    assert limiter.check("bob", cfg)[0] is True
    # Both should now be at limit
    assert limiter.check("alice", cfg)[0] is False
    assert limiter.check("bob", cfg)[0] is False


def test_window_expiry_clears_bucket(monkeypatch):
    """After the window passes, the bucket resets."""
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=1, window_seconds=1)
    assert limiter.check("user-x", cfg)[0] is True
    assert limiter.check("user-x", cfg)[0] is False

    # Advance fake time by sleeping just over the window.
    time.sleep(1.2)
    assert limiter.check("user-x", cfg)[0] is True


def test_gc_removes_idle_buckets():
    """GC sweep should drop empty buckets to prevent unbounded memory growth."""
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=10, window_seconds=1)
    # Populate many buckets
    for i in range(100):
        limiter.check(f"u-{i}", cfg)
    assert len(limiter._buckets) >= 100  # type: ignore[attr-defined]

    # Wait past the window
    time.sleep(1.2)
    # Force GC
    limiter._gc_empty_keys()  # type: ignore[attr-defined]
    # Idle buckets should be cleared
    assert len(limiter._buckets) == 0  # type: ignore[attr-defined]


def test_get_status_and_helper_functions():
    limiter = InMemoryRateLimiter()
    cfg = RateLimitConfig(max_requests=5, window_seconds=60)
    
    remaining, reset_in = limiter.get_status("user-status-test", cfg)
    assert remaining == 5
    assert reset_in == 60

    limiter.check("user-status-test", cfg)
    remaining, reset_in = limiter.get_status("user-status-test", cfg)
    assert remaining == 4
    assert reset_in <= 60

    # Test module-level functions
    rem, res = get_rate_limit_status("status-user-1", "test_action", max_requests=10, window_seconds=60)
    assert rem == 10

    check_rate_limit("limit-user-1", "test_action", max_requests=1, window_seconds=60)
    with pytest.raises(HTTPException) as exc_info:
        check_rate_limit("limit-user-1", "test_action", max_requests=1, window_seconds=60)
    assert exc_info.value.status_code == 429
