import random
import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fuzzyopt import levenshtein, levenshtein_bounded


class DistanceTests(unittest.TestCase):
    def test_known_distances(self):
        cases = [
            ("", "", 0), ("kitten", "sitting", 3),
            ("book", "back", 2), ("猫咪", "猫", 1),
            ("東京", "京都", 2), ("你好", "您好", 1),
            ("café", "cafe", 1),
        ]
        for a, b, expected in cases:
            with self.subTest(a=a, b=b):
                self.assertEqual(levenshtein(a, b), expected)

    def test_bounded_matches_reference_for_random_inputs(self):
        rng = random.Random(20261017)
        alphabet = "abcxyz你好世界日本語é中🙂"
        for _ in range(2500):
            a = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 14)))
            b = "".join(rng.choice(alphabet) for _ in range(rng.randrange(0, 14)))
            exact = levenshtein(a, b)
            for threshold in range(0, 5):
                got = levenshtein_bounded(a, b, threshold)
                expected = exact if exact <= threshold else threshold + 1
                self.assertEqual(got, expected, (a, b, threshold, exact, got))

    def test_band_fallback_matches_reference(self):
        # Short strings and large thresholds fall back to the plain row DP;
        # long strings with small thresholds take the banded path. Both must
        # agree with the reference implementation.
        cases = [
            ("张三丰", "张小丰"), ("ab", "ba"), ("東京", "京都"),
            ("abcdefgh", "abcdefgx"), ("a" * 40, "a" * 39 + "b"),
        ]
        for a, b in cases:
            exact = levenshtein(a, b)
            for threshold in range(0, 6):
                with self.subTest(a=a[:6], b=b[:6], threshold=threshold):
                    got = levenshtein_bounded(a, b, threshold)
                    expected = exact if exact <= threshold else threshold + 1
                    self.assertEqual(got, expected)

    def test_threshold_validation(self):
        for value in (-1,):
            with self.assertRaises(ValueError):
                levenshtein_bounded("a", "b", value)
        for value in (1.5, True, "2"):
            with self.assertRaises(TypeError):
                levenshtein_bounded("a", "b", value)


if __name__ == "__main__":
    unittest.main()
