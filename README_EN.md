# Fuzzy Search Lab

A dependency-free Python fuzzy-search index: threshold-aware Levenshtein distance,
length bucketing, and Unicode normalization, for typo-tolerant lookup over names,
titles, and small-to-medium vocabularies.

**Correctness first, speed claims second.** Every optimization is checked against a
plain reference implementation, and the benchmarks fail loudly if the two ever return
different result sets. No runtime dependencies, Python 3.10+.

## Run

```bash
python examples/demo.py
python -m unittest discover -s tests -v
python benchmarks/benchmark.py
python benchmarks/shape_matrix.py
```

## What it does

- Length-difference pruning, banded dynamic programming, and row-minimum early exit.
  When the band would cover the whole matrix, it falls back to the plain DP.
- NFC + `casefold()` by default; `FuzzySearchIndex(values, compatibility=True)` opts
  into NFKC, which also folds full-width forms (`ＡＢＣ` -> `ABC`, `ｶﾀｶﾅ` -> `カタカナ`)
  and other compatibility characters (`①` -> `1`, `ﬁ` -> `fi`).
- Results are ordered by edit distance, then by original input position.

## Performance depends on corpus shape

Measured on CPython 3.13.14 / Windows 11 x64, 12,000 items, 6 queries, `k=2`, both
implementations interleaved and reported as medians against a pre-normalized
plain-DP baseline:

| Corpus shape | Distinct lengths | Still scanned after bucketing | Baseline | This index | Speedup |
|---|---|---|---|---|---|
| Latin product names (22–55 chars) | 34 | 29.1% | 6,602 ms | 59.2 ms | **112×** |
| CJK product names (10–16 chars) | 7 | 72.7% | 980 ms | 138.1 ms | **7.1×** |
| Japanese titles (14–17 chars) | 4 | 97.9% | 1,263 ms | 182.3 ms | **6.9×** |
| CJK names (2–3 chars) | 2 | 100% | 204.9 ms | 202.5 ms | **1.01×** |

Length bucketing can only prune when the corpus has varied lengths. For 2–3 character
names every value falls inside ±k, so the index degrades to the baseline instead of
speeding it up. Speedup is machine-specific; rerun `shape_matrix.py` on your own data.

This is an independent implementation, not a fork of uFuzzy, Fuse.js, or RapidFuzz,
and it does not copy their source files. See `UPSTREAM_NOTES.md` for the research
references and the source statement. MIT License; see `LICENSE`.
