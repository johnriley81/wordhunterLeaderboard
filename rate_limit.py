"""Simple in-process IP rate limiting (one request per method per 60 seconds)."""

from __future__ import annotations

import time
from threading import Lock

RATE_LIMIT_SECONDS = 60

_lock = Lock()
_last_request_at: dict[str, float] = {}


def _rate_limit_key(client_ip: str, method: str) -> str:
    ip = str(client_ip or "unknown").strip() or "unknown"
    http_method = str(method or "GET").strip().upper() or "GET"
    return f"{http_method}:{ip}"


def check_rate_limit(client_ip: str, method: str = "GET") -> bool:
    """Return True when the request is allowed."""
    key = _rate_limit_key(client_ip, method)
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
