"""Simple in-process IP rate limiting (one request per minute)."""

from __future__ import annotations

import time
from threading import Lock

RATE_LIMIT_SECONDS = 60

_lock = Lock()
_last_request_at: dict[str, float] = {}


def check_rate_limit(client_ip: str) -> bool:
    """Return True when the request is allowed."""
    key = str(client_ip or "unknown").strip() or "unknown"
    now = time.monotonic()
    with _lock:
        last = _last_request_at.get(key)
        if last is not None and now - last < RATE_LIMIT_SECONDS:
            return False
        _last_request_at[key] = now
        return True


def reset_rate_limits_for_tests() -> None:
    with _lock:
        _last_request_at.clear()
