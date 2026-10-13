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
        settings = request.app.state.settings
        # Keyed on whichever credential the caller presented, hashed so the raw
        # key or session token never lands in the limiter's keys. A login
        # attempt has neither yet, so those share the IP-only budget.
        credential = request.headers.get("x-api-key") or request.cookies.get(
            settings.auth_cookie_name
        )
        key_id = hashlib.sha256((credential or "anonymous").encode()).hexdigest()[:16]
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
    """Limit one operation. `upload` and `reanalyze` keep their Milestone 9 budgets.

    `login` and `register` are limited harder and, having no credential yet,
    are effectively bounded by client IP, which is what a password-guessing
    attempt actually looks like from here.
    """
    settings = request.app.state.settings
    limits = {
        "upload": settings.upload_rate_limit,
        "reanalyze": settings.reanalyze_rate_limit,
        "login": settings.login_rate_limit,
        "register": settings.login_rate_limit,
    }
    request.app.state.rate_limiter.check(
        request,
        operation=operation,
        limit=limits.get(operation, settings.upload_rate_limit),
        window_seconds=settings.rate_limit_window_seconds,
    )
