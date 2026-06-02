"""Shared leaderboard validation and DB insert helpers."""

from __future__ import annotations

import re

from better_profanity import profanity
from wordhunter_scoring import iter_tiles, score_word_for_validation

_NAME_SANITIZE_RE = re.compile(r"[^a-zA-Z]")
_UUID_RE = re.compile(
    r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$"
)
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


def _consume_word_tiles_from_pool(pool: list[str], word: str) -> bool:
    for tile in iter_tiles(word):
        key = str(tile or "").lower()
        try:
            pool.remove(key)
        except ValueError:
            return False
    return True


def validate_score_payload(payload, submitted_score: int, trophy: str) -> int:
    """Validate words against gameLetters and return computed score, or 0 if invalid."""
    if not isinstance(payload, dict):
        return 0

    game_letters = payload.get("gameLetters")
    words_played = payload.get("wordsPlayed")
    if not isinstance(game_letters, list) or not isinstance(words_played, list):
        return 0
    if not words_played:
        return 0

    pool = [str(t or "").lower() for t in game_letters]
    score = 0
    trophy_found = False
    trophy_norm = str(trophy or "").strip().lower()

    for raw_word in words_played:
        word = str(raw_word or "").lower()
        if not word:
            return 0
        if word == trophy_norm:
            trophy_found = True
        if not _consume_word_tiles_from_pool(pool, word):
            return 0
        try:
            score += score_word_for_validation(word)
        except (KeyError, ValueError):
            return 0

    if not trophy_found:
        return 0
    if score != int(submitted_score):
        return 0
    return score


def normalize_session_id(session_id) -> str | None:
    if session_id is None:
        return None
    value = str(session_id).strip()
    if not value or not _UUID_RE.match(value):
        return None
    return value.lower()


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


def try_upsert_leaderboard_session(
    cur, conn, puzzle, time_stamp, player, score, trophy, session_id
):
    cur.execute(
        "SELECT score FROM leaderboard WHERE puzzle=%s AND session_id=%s",
        (puzzle, session_id),
    )
    row = cur.fetchone()
    if row is None:
        cur.execute(
            "INSERT INTO leaderboard (puzzle, time, player, score, trophy, session_id) "
            "VALUES (%s, %s, %s, %s, %s, %s)",
            (puzzle, time_stamp, player, score, trophy, session_id),
        )
        conn.commit()
        return "Record inserted successfully."
    existing_score = int(row[0])
    if score > existing_score:
        cur.execute(
            "UPDATE leaderboard SET time=%s, player=%s, score=%s, trophy=%s "
            "WHERE puzzle=%s AND session_id=%s",
            (time_stamp, player, score, trophy, puzzle, session_id),
        )
        conn.commit()
        return "Record updated successfully."
    return "Score not improved."


def try_save_leaderboard(
    cur, conn, puzzle, time_stamp, player, score, trophy, session_id_raw=None
):
    session_id = normalize_session_id(session_id_raw)
    if session_id:
        return try_upsert_leaderboard_session(
            cur, conn, puzzle, time_stamp, player, score, trophy, session_id
        )
    return try_insert_leaderboard(cur, conn, puzzle, time_stamp, player, score, trophy)
