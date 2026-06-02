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

    def test_perfect_hunt_puzzle_14_accepts_without_letter_pool(self):
        payload = {
            "gameLetters": [
                "a",
                "w",
                "d",
                "e",
                "y",
                "i",
                "i",
                "e",
                "o",
                "r",
                "s",
                "p",
                "c",
                "e",
                "r",
                "c",
                "d",
                "o",
                "n",
                "f",
                "n",
                "g",
                "s",
                "r",
                "t",
                "r",
                "g",
                "a",
                "i",
                "z",
                "e",
                "d",
                "e",
                "e",
                "v",
                "l",
                "n",
                "c",
                "k",
                "o",
                "l",
                "e",
                "a",
                "t",
                "a",
                "t",
                "c",
                "a",
                "s",
                "i",
                "qu",
                "l",
                "z",
                "i",
                "n",
                "o",
                "y",
                "c",
                "i",
                "m",
                "i",
                "v",
                "e",
                "",
                "",
                "r",
                "",
                "",
                "",
                "l",
                "",
                "h",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
                "",
            ],
            "wordsPlayed": [
                "speedway",
                "recordings",
                "confederation",
                "legalization",
                "quicksilver",
                "victimization",
                "hierarchically",
            ],
        }
        self.assertEqual(validate_score_payload(payload, 1861, "hierarchically"), 1861)

    def test_rejects_when_score_mismatch(self):
        payload = {
            "gameLetters": ["l", "e", "v", "e", "l"],
            "wordsPlayed": ["level"],
        }
        self.assertEqual(validate_score_payload(payload, 41, "level"), 0)

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

    def test_allows_first_then_blocks_within_window_for_same_method(self):
        ip = "203.0.113.1"
        self.assertTrue(check_rate_limit(ip, "GET"))
        self.assertFalse(check_rate_limit(ip, "GET"))

    def test_get_then_post_both_allowed_in_quick_succession(self):
        ip = "203.0.113.2"
        self.assertTrue(check_rate_limit(ip, "GET"))
        self.assertTrue(check_rate_limit(ip, "POST"))

    def test_post_then_get_both_allowed_in_quick_succession(self):
        ip = "203.0.113.3"
        self.assertTrue(check_rate_limit(ip, "POST"))
        self.assertTrue(check_rate_limit(ip, "GET"))


if __name__ == "__main__":
    unittest.main()
