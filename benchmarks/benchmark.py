"""Reproducible baseline-vs-optimized benchmark (standard library only)."""
from __future__ import annotations

import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fuzzyopt import FuzzySearchIndex, levenshtein, normalize  # noqa: E402


def make_corpus(size: int = 12000, seed: int = 20261017) -> list[str]:
    rng = random.Random(seed)
    syllables = [
        "search", "router", "planet", "travel", "photo", "archive", "music",
        "算法", "搜索", "图片", "日本語", "東京", "你好", "星球", "数据", "缓存",
        "快速", "索引", "文本", "中文", "kotlin", "python", "rust", "javascript",
    ]
    corpus = []
    for i in range(size):
        base = "".join(rng.choice(syllables) for _ in range(rng.randint(1, 3)))
        corpus.append(f"{base}-{i % 997:03d}")
    return corpus


def baseline_search(query: str, corpus: list[str], threshold: int):
    """Simple exhaustive baseline: calculate full distance for every value."""
    normalized_query = normalize(query)
    result = []
    for i, value in enumerate(corpus):
        candidate = normalize(value)
        distance = levenshtein(normalized_query, candidate)
        if distance <= threshold:
            result.append((distance, i, value))
    result.sort(key=lambda item: (item[0], item[1]))
    return result


def optimized_search(query: str, index: FuzzySearchIndex, threshold: int):
    return [(m.distance, m.index, m.value)
            for m in index.search(query, max_distance=threshold, limit=None)]


def time_once(fn, repeats: int) -> tuple[float, object]:
    samples = []
    output = None
    for _ in range(repeats):
        started = time.perf_counter()
        output = fn()
        samples.append(time.perf_counter() - started)
    return statistics.median(samples), output


def main() -> None:
    corpus = make_corpus()
    queries = ["serch-014", "星球-123", "pythno-021", "東京-500"]
    threshold = 2
    repeats = 3

    started = time.perf_counter()
    index = FuzzySearchIndex(corpus)
    index_build = time.perf_counter() - started

    baseline_seconds = 0.0
    optimized_seconds = 0.0
    for query in queries:
        base_time, base_result = time_once(
            lambda q=query: baseline_search(q, corpus, threshold), repeats
        )
        fast_time, fast_result = time_once(
            lambda q=query: optimized_search(q, index, threshold), repeats
        )
        if base_result != fast_result:
            raise AssertionError(f"Results differ for {query!r}")
        baseline_seconds += base_time
        optimized_seconds += fast_time
        print(f"query={query!r}: baseline={base_time*1000:.2f} ms, "
              f"optimized={fast_time*1000:.2f} ms, matches={len(fast_result)}")

    ratio = baseline_seconds / optimized_seconds if optimized_seconds else float("inf")
    print("\n--- Summary (medians across repetitions) ---")
    print(f"corpus_items={len(corpus)} queries={len(queries)} threshold={threshold}")
    print(f"index_build={index_build*1000:.2f} ms")
    print(f"baseline_total={baseline_seconds*1000:.2f} ms")
    print(f"optimized_search_total={optimized_seconds*1000:.2f} ms")
    print(f"search_speedup={ratio:.2f}x (excludes index build)")
    print("Note: hardware/runtime-specific; rerun locally before publishing claims.")


if __name__ == "__main__":
    main()
