"""Puzzle id alignment with the Wordhunter client calendar."""

from __future__ import annotations

from datetime import date

# Local calendar days; client should use the same midnight boundary in its timezone.
PUZZLE_ROTATION_EPOCH = date(2026, 4, 26)


def day_index_since_rotation(d: date) -> int:
    """Whole calendar days since ``PUZZLE_ROTATION_EPOCH`` (that date = index 0)."""
    return (d - PUZZLE_ROTATION_EPOCH).days


def template_row_index(puzzle_id: int, pool_size: int) -> int:
    """Row in ``nextletters.txt`` / ``puzzles.txt`` pool: ``puzzle_id % pool_size``."""
    if pool_size <= 0:
        raise ValueError("pool_size must be positive")
    return puzzle_id % pool_size
