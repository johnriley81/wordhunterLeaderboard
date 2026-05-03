"""Runtime flags (env)."""

from __future__ import annotations

import os


def score_trace_validation_enabled() -> bool:
    """When True, POST requires ``scoreValidation`` and runs ``validate_game``."""
    v = os.environ.get("WORDHUNTER_VALIDATE_SCORE", "")
    return v.lower() in ("1", "true", "yes")
