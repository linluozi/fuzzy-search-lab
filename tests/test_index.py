import unittest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fuzzyopt import FuzzySearchIndex, levenshtein, normalize


class IndexTests(unittest.TestCase):
    def test_typo_and_stable_order(self):
        index = FuzzySearchIndex(["apple", "apply", "apples", "banana"])
        results = index.search("appl", max_distance=1, limit=None)
        self.assertEqual([m.value for m in results], ["apple", "apply"])
        self.assertEqual([m.distance for m in results], [1, 1])
        self.assertEqual([m.index for m in results], [0, 1])

    def test_multilingual_and_unicode_equivalence(self):
        words = ["你好世界", "您好世界", "東京", "カタカナ", "café", "Straße"]
        index = FuzzySearchIndex(words)
        self.assertEqual(index.search("你好世間", max_distance=1)[0].value, "你好世界")
        self.assertEqual(index.search("cafe\u0301", max_distance=0)[0].value, "café")
        self.assertEqual(index.search("STRASSE", max_distance=0)[0].value, "Straße")
        self.assertEqual(normalize("e\u0301"), normalize("é"))

    def test_compatibility_folding_is_opt_in(self):
        plain = FuzzySearchIndex(["ABC", "カタカナ"])
        self.assertEqual(plain.search("ＡＢＣ", max_distance=0), [])
        self.assertEqual(plain.search("ｶﾀｶﾅ", max_distance=0), [])

        wide = FuzzySearchIndex(["ABC", "カタカナ"], compatibility=True)
        self.assertEqual(wide.search("ＡＢＣ", max_distance=0)[0].value, "ABC")
        self.assertEqual(wide.search("ｶﾀｶﾅ", max_distance=0)[0].value, "カタカナ")
        # NFKC also folds characters that are not visually identical, which is
        # exactly why it stays opt-in.
        self.assertEqual(
            FuzzySearchIndex(["1"], compatibility=True).search("①", max_distance=0)[0].value, "1"
        )

    def test_limits_and_empty_query(self):
        index = FuzzySearchIndex(["", "a", "b", "ab"])
        self.assertEqual(index.search("a", max_distance=1, limit=0), [])
        self.assertEqual(len(index.search("a", max_distance=1, limit=2)), 2)
        self.assertEqual(index.search("", max_distance=0, limit=None)[0].value, "")

    def test_limit_zero_still_validates_the_query(self):
        index = FuzzySearchIndex(["ok"])
        with self.assertRaises(TypeError):
            index.search(123, limit=0)
        self.assertEqual(index.search("ok", limit=0), [])

    def test_huge_threshold_matches_reference(self):
        words = ["", "a", "ab", "abc", "abcd", "日本語", "東京", "京都"]
        words += [f"item{i:02d}" for i in range(40)]
        index = FuzzySearchIndex(words)
        for query in ("abc", "", "東京x", "zzz"):
            got = [(m.distance, m.index)
                   for m in index.search(query, max_distance=1000, limit=None)]
            nq = normalize(query)
            want = sorted(
                (levenshtein(nq, normalize(word)), i) for i, word in enumerate(words)
            )
            self.assertEqual(got, want)

    def test_validates_values_and_options(self):
        with self.assertRaises(TypeError):
            FuzzySearchIndex(["ok", 5])
        with self.assertRaises(TypeError):
            FuzzySearchIndex([None])
        with self.assertRaises(TypeError):
            FuzzySearchIndex("abc")
        with self.assertRaises(TypeError):
            FuzzySearchIndex(["ok"], compatibility=1)
        index = FuzzySearchIndex(["ok"])
        with self.assertRaises(ValueError):
            index.search("ok", max_distance=-1)
        with self.assertRaises(ValueError):
            index.search("ok", limit=-1)


if __name__ == "__main__":
    unittest.main()
