"""Shared leaderboard validation and next-letter loading."""

from __future__ import annotations

from collections import deque
import json

from puzzle_calendar import template_row_index
from wordhunter_scoring import score_word_for_validation


def validate_turn(word, letters, replacement_count, next_letters):
    for letter in set(word):
        if letter not in letters:
            return False, None

    validation_board = list(letters)
    for letter in set(word):
        if letter in validation_board:
            validation_board.remove(letter)

    for _ in range(replacement_count):
        if next_letters:
            validation_board.append(next_letters.popleft())
        else:
            validation_board.append(" ")

    return True, "".join(validation_board)


def validate_game(validation_data, next_letters, trophy):
    trophy_found = False
    if not validation_data:
        return 0
    score = 0
    next_letters = deque(next_letters)
    for idx, turn_data in enumerate(validation_data):
        word, letters, replacement_count = turn_data
        if word == trophy:
            trophy_found = True
        if replacement_count < 3:
            return 0
        score += score_word_for_validation(word)
        is_valid, validation_board = validate_turn(
            word, letters, replacement_count, next_letters
        )
        if not is_valid:
            return 0

        if idx + 1 < len(validation_data):
            next_turn_letters = set(validation_data[idx + 1][1])
            if not all(letter in validation_board for letter in next_turn_letters):
                return 0

    if trophy_found:
        return score
    return 0


def get_next_letters(puzzle_id: int, *, path: str = "nextletters.txt"):
    with open(path, "r", encoding="utf-8") as file:
        lines = file.readlines()
    row = template_row_index(puzzle_id, len(lines))
    return json.loads(lines[row].strip())


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
