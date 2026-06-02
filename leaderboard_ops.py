"""Shared leaderboard validation and DB insert helpers."""

from __future__ import annotations

import re

from better_profanity import profanity
from wordhunter_scoring import score_word_for_validation

_NAME_SANITIZE_RE = re.compile(r"[^a-zA-Z]")
_MAX_PLAYER_NAME_LEN = 8

# Uppercase names that pass sanitize but must not appear on the leaderboard.
_PROHIBITED_LEADERBOARD_NAMES = frozenset(
    {
        "FUCK",
        "SHIT",
        "CUNT",
        "NIGGER",
        "NIGGA",
        "FAGGOT",
        "FAG",
        "RETARD",
        "WHORE",
        "SLUT",
        "BITCH",
        "ASSHOLE",
        "DICK",
        "COCK",
        "PENIS",
        "VAGINA",
        "NAZI",
        "KKK",
    }
)


def normalize_player_name(player: str) -> str:
    return _NAME_SANITIZE_RE.sub("", str(player or "")).upper()[:_MAX_PLAYER_NAME_LEN]


def validate_player_name(player: str) -> str | None:
    """Return an error message when the name is not allowed, else None."""
    raw = str(player or "")
    if not raw.strip():
        return "Invalid player name: empty"
    if profanity.contains_profanity(raw):
        return f"Invalid player name: {raw} (profanity)"
    normalized = normalize_player_name(raw)
    if not normalized:
        return f"Invalid player name: {raw}"
    if normalized in _PROHIBITED_LEADERBOARD_NAMES:
        return f"Invalid player name: {raw} (prohibited)"
    return None


def validate_score_payload(payload, submitted_score: int, trophy: str) -> int:
    """Validate wordsPlayed + trophy and return computed score, or 0 if invalid."""
    if not isinstance(payload, dict):
        return 0

    words_played = payload.get("wordsPlayed")
    if not isinstance(words_played, list) or not words_played:
        return 0

    score = 0
    trophy_found = False
    trophy_norm = str(trophy or "").strip().lower()

    for raw_word in words_played:
        word = str(raw_word or "").lower()
        if not word:
            return 0
        if word == trophy_norm:
            trophy_found = True
        try:
            score += score_word_for_validation(word)
        except (KeyError, ValueError):
            return 0

    if not trophy_found:
        return 0
    if score != int(submitted_score):
        return 0
    return score


def try_insert_leaderboard(cur, conn, puzzle, time_stamp, player, score, trophy):
    cur.execute(
        f"SELECT COUNT(*) FROM leaderboard WHERE puzzle={puzzle} AND player='{player}' AND score={score} AND trophy='{trophy}'"
    )
    if cur.fetchone()[0] == 0:
        cur.execute(
            f"INSERT INTO leaderboard (puzzle, time, player, score, trophy) VALUES ({puzzle}, {time_stamp}, '{player}', {score}, '{trophy}')"
        )
        conn.commit()
        return "Record inserted successfully."
    return "This record already exists."
