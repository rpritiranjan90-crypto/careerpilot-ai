"""Rate limiting utilities.

Provides an in-process sliding-window rate limiter using consistent monotonic time.
In production with multiple replica instances, use a shared store (Redis/Valkey).
"""

from __future__ import annotations

import threading
import time
from collections import defaultdict
from dataclasses import dataclass

from fastapi import HTTPException, status


@dataclass(frozen=True)
class RateLimitConfig:
    """Configuration for a rate limit window."""

    max_requests: int
    window_seconds: int = 3600  # Default 1 hour


class InMemoryRateLimiter:
    """Thread-safe in-memory sliding-window rate limiter.

    Uses `time.monotonic()` exclusively to avoid wall-clock shifts (NTP, leap seconds).
    """

    def __init__(self, gc_interval_seconds: float = 300.0) -> None:
        self._buckets: dict[str, list[float]] = defaultdict(list)
        self._bucket_windows: dict[str, float] = {}
        self._lock = threading.Lock()
        self._gc_interval = gc_interval_seconds
        self._last_gc: float = time.monotonic()

    def _gc_empty_keys(self, max_age_seconds: float | None = None) -> None:
        """Purge expired timestamps and delete empty user buckets."""
        now = time.monotonic()
        self._last_gc = now
        empty_keys = []
        with self._lock:
            for key, timestamps in list(self._buckets.items()):
                window = (
                    max_age_seconds
                    if max_age_seconds is not None
                    else self._bucket_windows.get(key, 3600.0)
                )
                cutoff = now - window
                pruned = [t for t in timestamps if t > cutoff]
                if not pruned:
                    empty_keys.append(key)
                else:
                    self._buckets[key] = pruned
            for key in empty_keys:
                self._buckets.pop(key, None)
                self._bucket_windows.pop(key, None)

    def check(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> tuple[bool, int | None]:
        """Check if request for `key` is permitted under `config`.

        Returns:
            Tuple of (is_allowed, retry_after_seconds_or_none)
        """
        now = time.monotonic()
        cutoff = now - config.window_seconds

        with self._lock:
            self._bucket_windows[key] = float(config.window_seconds)
            valid_timestamps = [t for t in self._buckets[key] if t > cutoff]
            self._buckets[key] = valid_timestamps

            if len(valid_timestamps) >= config.max_requests:
                oldest = valid_timestamps[0]
                retry_after = max(1, int(config.window_seconds - (now - oldest)))
                return False, retry_after

            self._buckets[key].append(now)

            if now - self._last_gc >= self._gc_interval:
                # Run GC inline if interval exceeded
                pass

        if now - self._last_gc >= self._gc_interval:
            self._gc_empty_keys()

        return True, None

    def get_status(
        self,
        key: str,
        config: RateLimitConfig,
    ) -> tuple[int, int]:
        """Get remaining requests and seconds until reset."""
        now = time.monotonic()
        cutoff = now - config.window_seconds

        with self._lock:
            self._bucket_windows[key] = float(config.window_seconds)
            valid_timestamps = [t for t in self._buckets[key] if t > cutoff]
            self._buckets[key] = valid_timestamps

            used = len(valid_timestamps)
            remaining = max(0, config.max_requests - used)

            if valid_timestamps:
                oldest = valid_timestamps[0]
                reset_in = max(0, int(config.window_seconds - (now - oldest)))
            else:
                reset_in = config.window_seconds

            return remaining, reset_in


# Global singleton instance
_default_limiter = InMemoryRateLimiter()
WINDOW_SECONDS = 3600


def check_rate_limit(
    user_id: str,
    action: str,
    max_requests: int,
    window_seconds: int = WINDOW_SECONDS,
) -> None:
    """Check if user has exceeded rate limit for an action.

    Args:
        user_id: Unique user identifier
        action: Action type (e.g., "analyze", "interview")
        max_requests: Maximum requests allowed per window
        window_seconds: Length of the rate limit window in seconds

    Raises:
        HTTPException with 429 status if limit exceeded
    """
    key = f"{user_id}:{action}"
    config = RateLimitConfig(max_requests=max_requests, window_seconds=window_seconds)
    allowed, retry_after = _default_limiter.check(key, config)

    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Try again in {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )


def get_rate_limit_status(
    user_id: str,
    action: str,
    max_requests: int,
    window_seconds: int = WINDOW_SECONDS,
) -> tuple[int, int]:
    """Get current rate limit status.

    Returns:
        Tuple of (remaining_requests, seconds_until_reset)
    """
    key = f"{user_id}:{action}"
    config = RateLimitConfig(max_requests=max_requests, window_seconds=window_seconds)
    return _default_limiter.get_status(key, config)
