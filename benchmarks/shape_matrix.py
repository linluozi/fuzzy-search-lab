"""Compare the index against a careful baseline across corpus shapes.

The bundled ``benchmark.py`` uses one synthetic corpus whose lengths are spread
over 24 values, which is the best case for length bucketing. Real corpora often
cluster instead: Chinese person names are 2-3 characters, product titles are
10-16. This script measures four shapes and reports how much the index actually
buys on each one.

Both implementations are interleaved per round so CPU frequency drift and
background load hit them equally. Results are asserted to be identical.

Run::

    python benchmarks/shape_matrix.py
    python benchmarks/shape_matrix.py --size 20000 --queries 8 --rounds 5
"""
from __future__ import annotations

import argparse
import random
import statistics
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fuzzyopt import FuzzySearchIndex, levenshtein, normalize  # noqa: E402


def make_latin_products(size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    brands = ["Acme", "Northwind", "Globex", "Initech", "Umbrella", "Soylent", "Vehement"]
    categories = ["Wireless Earbuds", "Mechanical Keyboard", "Power Bank", "USB-C Cable",
                  "Monitor Stand", "Noise Cancelling Headphones", "Fast Charger", "Webcam"]
    attributes = ["Long Battery", "Silent", "Fast Charge", "Portable", "White", "Black",
                  "Pro Edition", "Starter Kit", "Bundle", "2026 Model"]
    return [f"{rng.choice(brands)} {rng.choice(categories)} {rng.choice(attributes)} "
            f"#{i % 1000:03d}" for i in range(size)]


def make_cjk_products(size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    brands = ["小米", "华为", "联想", "罗技", "安克", "绿联", "倍思", "雷蛇", "漫步者", "飞利浦"]
    categories = ["无线蓝牙耳机", "机械键盘", "移动电源", "数据线", "显示器支架",
                  "鼠标垫", "降噪耳机", "充电器", "摄像头", "音箱"]
    attributes = ["长续航", "静音", "快充", "便携", "白色", "黑色", "旗舰版", "入门版", "套装", "新款"]
    return [f"{rng.choice(brands)}{rng.choice(categories)} {rng.choice(attributes)}"
            f"{i % 1000:03d}" for i in range(size)]


def make_cjk_names(size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    surnames = ["王", "李", "张", "刘", "陈", "杨", "黄", "赵", "周", "吴",
                "徐", "孙", "马", "朱", "胡", "郭", "何", "高", "林", "罗"]
    given = ["伟", "芳", "娜", "敏", "静", "强", "磊", "洋", "艳", "勇", "军", "杰", "娟",
             "涛", "明", "超", "霞", "平", "刚", "桂", "文", "辉", "玲", "鹏", "华", "红",
             "玉", "波", "斌", "宁"]
    names: set[str] = set()
    while len(names) < size:
        two = rng.random() < 0.62
        names.add(f"{rng.choice(surnames)}{rng.choice(given)}"
                  f"{rng.choice(given) if two else ''}")
    return list(names)


def make_japanese_titles(size: int, seed: int) -> list[str]:
    rng = random.Random(seed)
    places = ["东京", "京都", "大阪", "北海道", "冲绳", "奈良", "神户", "名古屋"]
    kinds = ["旅行指南", "美食地图", "住宿推荐", "交通攻略", "景点清单", "购物手册",
             "温泉笔记", "摄影路线"]
    editions = ["2026版", "完全版", "口袋版", "图解版", "增补版", "典藏版"]
    return [f"{rng.choice(places)}{rng.choice(kinds)} {rng.choice(editions)} "
            f"{i % 997:03d}" for i in range(size)]


SHAPES = {
    "latin_products": (make_latin_products,
                       ["Acme Wireless Earbuds Long Battery #00X",
                        "Globex Mechanical Keyboard Silent #0X2",
                        "Initech Power Bank Fast Charge #00X",
                        "Umbrella USB-C Cable Portable #0X5"]),
    "cjk_products": (make_cjk_products,
                     ["小米无线蓝牙耳机 长续航001X",
                      "联想机械键盘 静音0X2",
                      "安克移动电源 快充00X",
                      "绿联数据线 便携0X5"]),
    "japanese_titles": (make_japanese_titles,
                        ["东京旅行指南 2026版 00X",
                         "京都美食地图 完全版 0X2",
                         "大阪住宿推荐 口袋版 00X",
                         "北海道交通攻略 图解版 0X5"]),
    "cjk_names": (make_cjk_names, ["王伟X", "李X芳", "张X娜", "陈静X"]),
}


def baseline_search(normalized: list[str], values: list[str], query: str, threshold: int):
    """Pre-normalized corpus + plain full-matrix DP, same output shape."""
    normalized_query = normalize(query)
    out = []
    for index, candidate in enumerate(normalized):
        distance = levenshtein(normalized_query, candidate)
        if distance <= threshold:
            out.append((distance, index, values[index]))
    out.sort(key=lambda item: (item[0], item[1]))
    return out


def index_search(index: FuzzySearchIndex, query: str, threshold: int):
    return [(match.distance, match.index, match.value)
            for match in index.search(query, max_distance=threshold, limit=None)]


def scan_share(normalized: list[str], queries: list[str], threshold: int) -> float:
    total = len(normalized)
    shares = []
    for query in queries:
        query_length = len(normalize(query))
        shares.append(sum(1 for value in normalized
                          if abs(len(value) - query_length) <= threshold) / total)
    return statistics.mean(shares)


def run_shape(name, builder, queries, size, rounds, threshold):
    corpus = builder(size, seed=7)
    normalized = [normalize(value) for value in corpus]
    index = FuzzySearchIndex(corpus)

    expected = [baseline_search(normalized, corpus, query, threshold) for query in queries]
    got = [index_search(index, query, threshold) for query in queries]
    if got != expected:
        raise AssertionError(f"results differ for {name}")

    samples = {"baseline": [], "index": []}
    for _ in range(rounds):
        for label in ("baseline", "index"):
            started = time.perf_counter()
            if label == "baseline":
                for query in queries:
                    baseline_search(normalized, corpus, query, threshold)
            else:
                for query in queries:
                    index_search(index, query, threshold)
            samples[label].append(time.perf_counter() - started)

    baseline_time = statistics.median(samples["baseline"])
    index_time = statistics.median(samples["index"])
    lengths = {len(value) for value in normalized}
    return {
        "shape": name,
        "items": len(corpus),
        "lengths": len(lengths),
        "length_range": f"{min(lengths)}-{max(lengths)}",
        "scanned": scan_share(normalized, queries, threshold),
        "baseline": baseline_time,
        "index": index_time,
        "speedup": baseline_time / index_time if index_time else float("inf"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--size", type=int, default=6000, help="items per corpus")
    parser.add_argument("--queries", type=int, default=4, help="queries per corpus")
    parser.add_argument("--rounds", type=int, default=3, help="interleaved rounds")
    parser.add_argument("--threshold", type=int, default=2, help="edit distance threshold")
    args = parser.parse_args()

    rows = []
    for name, (builder, queries) in SHAPES.items():
        rows.append(run_shape(name, builder, queries[: args.queries], args.size,
                              args.rounds, args.threshold))

    print(f"\ncorpus={args.size} queries={args.queries} k={args.threshold} "
          f"rounds={args.rounds} (medians, interleaved)\n")
    print(f"{'shape':<17}{'lengths':>8}{'range':>8}{'scanned':>9}"
          f"{'baseline':>11}{'index':>10}{'speedup':>9}")
    for row in rows:
        print(f"{row['shape']:<17}{row['lengths']:>8}{row['length_range']:>8}"
              f"{row['scanned']*100:>8.1f}%{row['baseline']*1000:>10.1f}ms"
              f"{row['index']*1000:>9.1f}ms{row['speedup']:>8.2f}x")
    print("\n'scanned' is the share of items that length bucketing still has to"
          " visit; it is 100% when every value is within k of the query length.")
    print("Speedup is machine-specific. Rerun locally before quoting a number.")


if __name__ == "__main__":
    main()
