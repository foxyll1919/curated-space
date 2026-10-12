"""Small process-local fixed-window limiter for sensitive API operations."""

from __future__ import annotations

import hashlib
from threading import Lock
from time import monotonic

from fastapi import Request

from app.core.errors import RateLimitError


class FixedWindowRateLimiter:
    def __init__(self) -> None:
        self._lock = Lock()
        self._windows: dict[tuple[str, str], tuple[int, int]] = {}

    def check(self, request: Request, *, operation: str, limit: int, window_seconds: int) -> None:
        api_key = request.headers.get("x-api-key", "")
        key_id = hashlib.sha256(api_key.encode()).hexdigest()[:16]
        client_ip = request.client.host if request.client else "unknown"
        now = monotonic()
        window = int(now // window_seconds)
        identities = (("key", key_id), ("ip", client_ip))
        with self._lock:
            for kind, identity in identities:
                counter_key = (operation, f"{kind}:{identity}")
                old_window, count = self._windows.get(counter_key, (window, 0))
                if old_window != window:
                    count = 0
                if count >= limit:
                    raise RateLimitError()
                self._windows[counter_key] = (window, count + 1)
            # Bound stale entries without introducing a background task.
            if len(self._windows) > 10_000:
                self._windows = {
                    key: value for key, value in self._windows.items() if value[0] >= window - 1
                }


def enforce_rate_limit(request: Request, operation: str) -> None:
    settings = request.app.state.settings
    limit = settings.upload_rate_limit if operation == "upload" else settings.reanalyze_rate_limit
    request.app.state.rate_limiter.check(
        request,
        operation=operation,
        limit=limit,
        window_seconds=settings.rate_limit_window_seconds,
    )
