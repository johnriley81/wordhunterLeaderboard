import unittest
from unittest.mock import MagicMock

from leaderboard_ops import (
    normalize_session_id,
    try_save_leaderboard,
    try_upsert_leaderboard_session,
)


SESSION_A = "550e8400-e29b-41d4-a716-446655440000"


class NormalizeSessionIdTests(unittest.TestCase):
    def test_accepts_valid_uuid(self):
        self.assertEqual(
            normalize_session_id("550E8400-E29B-41D4-A716-446655440000"),
            SESSION_A,
        )

    def test_rejects_invalid(self):
        self.assertIsNone(normalize_session_id(""))
        self.assertIsNone(normalize_session_id("not-a-uuid"))
        self.assertIsNone(normalize_session_id(None))


class TryUpsertLeaderboardSessionTests(unittest.TestCase):
    def test_insert_when_no_existing_row(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = MagicMock()

        message = try_upsert_leaderboard_session(
            cur, conn, 7, 1000, "ADA", 50, "cat", SESSION_A
        )

        self.assertEqual(message, "Record inserted successfully.")
        self.assertEqual(cur.execute.call_count, 2)
        conn.commit.assert_called_once()

    def test_update_when_score_improves(self):
        cur = MagicMock()
        cur.fetchone.return_value = (40,)
        conn = MagicMock()

        message = try_upsert_leaderboard_session(
            cur, conn, 7, 1001, "BOB", 55, "dog", SESSION_A
        )

        self.assertEqual(message, "Record updated successfully.")
        self.assertEqual(cur.execute.call_count, 2)
        conn.commit.assert_called_once()

    def test_no_change_when_score_not_improved(self):
        cur = MagicMock()
        cur.fetchone.return_value = (50,)
        conn = MagicMock()

        message = try_upsert_leaderboard_session(
            cur, conn, 7, 1002, "ADA", 50, "cat", SESSION_A
        )

        self.assertEqual(message, "Score not improved.")
        self.assertEqual(cur.execute.call_count, 1)
        conn.commit.assert_not_called()

    def test_no_change_when_score_lower(self):
        cur = MagicMock()
        cur.fetchone.return_value = (60,)
        conn = MagicMock()

        message = try_upsert_leaderboard_session(
            cur, conn, 7, 1003, "ADA", 50, "cat", SESSION_A
        )

        self.assertEqual(message, "Score not improved.")
        conn.commit.assert_not_called()


class TrySaveLeaderboardTests(unittest.TestCase):
    def test_falls_back_to_legacy_insert_without_session_id(self):
        cur = MagicMock()
        cur.fetchone.return_value = (0,)
        conn = MagicMock()

        message = try_save_leaderboard(
            cur, conn, 7, 1000, "ADA", 50, "cat", session_id_raw=None
        )

        self.assertEqual(message, "Record inserted successfully.")
        conn.commit.assert_called_once()
        insert_sql = cur.execute.call_args_list[1][0][0]
        self.assertNotIn("session_id", insert_sql.lower())

    def test_uses_session_upsert_when_session_id_valid(self):
        cur = MagicMock()
        cur.fetchone.return_value = None
        conn = MagicMock()

        message = try_save_leaderboard(
            cur, conn, 7, 1000, "ADA", 50, "cat", session_id_raw=SESSION_A
        )

        self.assertEqual(message, "Record inserted successfully.")
        params = cur.execute.call_args_list[0][0][1]
        self.assertEqual(params[1], SESSION_A)


if __name__ == "__main__":
    unittest.main()
