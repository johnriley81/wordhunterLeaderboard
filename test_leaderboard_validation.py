import unittest

from leaderboard_ops import validate_player_name, validate_score_payload
from rate_limit import check_rate_limit, reset_rate_limits_for_tests


class ValidateScorePayloadTests(unittest.TestCase):
    def test_valid_level_consumes_duplicate_tiles(self):
        payload = {
            "gameLetters": ["l", "e", "v", "e", "l"],
            "wordsPlayed": ["level"],
        }
        self.assertEqual(validate_score_payload(payload, 40, "level"), 40)

    def test_rejects_when_letters_insufficient(self):
        payload = {
            "gameLetters": ["l", "e", "v", "l"],
            "wordsPlayed": ["level"],
        }
        self.assertEqual(validate_score_payload(payload, 40, "level"), 0)

    def test_requires_trophy_word_in_words_played(self):
        payload = {
            "gameLetters": ["c", "a", "t"],
            "wordsPlayed": ["cat"],
        }
        self.assertEqual(validate_score_payload(payload, 6, "dog"), 0)


class ValidatePlayerNameTests(unittest.TestCase):
    def test_prohibited_blocklist(self):
        self.assertIsNotNone(validate_player_name("FUCK"))

    def test_profanity(self):
        self.assertIsNotNone(validate_player_name("shithead"))


class RateLimitTests(unittest.TestCase):
    def setUp(self):
        reset_rate_limits_for_tests()

    def test_allows_first_then_blocks_within_window(self):
        ip = "203.0.113.1"
        self.assertTrue(check_rate_limit(ip))
        self.assertFalse(check_rate_limit(ip))


if __name__ == "__main__":
    unittest.main()
