"""Word scoring for server-side validation (wordhunter_cert parity).

Canonical rule (matches live client ``getLiveWordScoreBreakdownFromLabels``):
  wordTotal = letterSum * length
  - letterSum: sum of per-tile weights along the path (``qu`` is one tile).
  - length: sum of tile label string lengths (``qu`` counts as 2).

Weights default from ``tile_weights.json`` next to this module (replace with an export
from the game repo ``tools/wordhunter_cert`` when they differ). Override path with env
``WORDHUNTER_TILE_WEIGHTS_JSON``.
"""

from __future__ import annotations

import functools
import json
import os
from pathlib import Path


def iter_tiles(word: str) -> list[str]:
    """Segment played word into tiles left-to-right; ``qu`` is one tile (lowercase)."""
    w = (word or "").lower()
    tiles: list[str] = []
    i = 0
    while i < len(w):
        if i + 1 < len(w) and w[i] == "q" and w[i + 1] == "u":
            tiles.append("qu")
            i += 2
        else:
            tiles.append(w[i])
            i += 1
    return tiles


def _bundled_weights_path() -> Path:
    return Path(__file__).resolve().parent / "tile_weights.json"


@functools.lru_cache(maxsize=1)
def _tile_weights() -> dict[str, int]:
    path = os.environ.get("WORDHUNTER_TILE_WEIGHTS_JSON")
    if path and os.path.isfile(path):
        weights_path = Path(path)
    else:
        weights_path = _bundled_weights_path()
    if not weights_path.is_file():
        raise FileNotFoundError(
            f"Tile weights not found at {weights_path}; set WORDHUNTER_TILE_WEIGHTS_JSON "
            "or add tile_weights.json (vendored from tools/wordhunter_cert)."
        )
    with weights_path.open(encoding="utf-8") as f:
        raw = json.load(f)
    return {str(k).lower(): int(v) for k, v in raw.items()}


def score_word_for_validation(word: str) -> int:
    weights = _tile_weights()
    tiles = iter_tiles(word)
    length = sum(len(t) for t in tiles)
    letter_sum = 0
    for t in tiles:
        if t not in weights:
            raise KeyError(
                f"Tile {t!r} missing from tile weights; extend JSON to match wordhunter_cert."
            )
        letter_sum += weights[t]
    return letter_sum * length
