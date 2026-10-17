from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from fuzzyopt import FuzzySearchIndex, normalize

products = [
    "无线蓝牙耳机", "蓝牙音箱", "机械键盘", "便携显示器",
    "東京旅行指南", "Tokyo Travel Guide", "Café Latte Mug", "咖啡杯",
]
search = FuzzySearchIndex(products)

for query in ("无线蓝牙耳机", "无现蓝牙耳机", "tokyo travel guide", "cafe\u0301 latte mug"):
    print(f"\nQuery: {query}")
    for match in search.search(query, max_distance=2, limit=5):
        print(f"  {match.value!r} | distance={match.distance} | score={match.similarity:.3f}")

# Full-width input is not folded by default: NFC keeps ＡＢＣ and ABC distinct.
print("\nDefault (NFC):", normalize("ＡＢＣ"), "->", search.search("ＡＢＣ", max_distance=0))

# Opt into NFKC when your input comes from a full-width IME.
compat = FuzzySearchIndex(["ABC", "カタカナ"], compatibility=True)
print("compatibility=True:", [m.value for m in compat.search("ＡＢＣ", max_distance=0)],
      [m.value for m in compat.search("ｶﾀｶﾅ", max_distance=0)])
