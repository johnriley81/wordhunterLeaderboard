import unittest
from datetime import date

from puzzle_calendar import PUZZLE_ROTATION_EPOCH, day_index_since_rotation


class PuzzleCalendarTests(unittest.TestCase):
    def test_rotation_epoch_matches_word_hunter_client(self):
        self.assertEqual(PUZZLE_ROTATION_EPOCH, date(2026, 5, 19))

    def test_epoch_day_is_index_zero(self):
        self.assertEqual(day_index_since_rotation(date(2026, 5, 19)), 0)

    def test_next_day_increments_index(self):
        self.assertEqual(day_index_since_rotation(date(2026, 5, 20)), 1)


if __name__ == "__main__":
    unittest.main()
