# Changelog

## 0.1.0 — 2026-10-17

- Exact and threshold-bounded Levenshtein distance: length pruning, banded dynamic
  programming, and row-minimum early exit.
- Plain-DP fallback when the band would span most of the matrix, so short strings with
  a large `max_distance` no longer pay for empty boundary checks.
- Bucket-skip and bucket-key iteration in `search`: no `O(max_distance)` length loop,
  and no bucket indirection when every entry is already a candidate.
- Unicode NFC + `casefold()` normalization, with opt-in NFKC compatibility folding for
  full-width and compatibility characters (`compatibility=True`).
- Immutable, length-bucketed index with bounded top-k collection (`heapq.nsmallest`)
  when `limit` is set.
- Input validation: a single `str` is rejected instead of being read as a sequence of
  characters; `limit=0` no longer skips query validation.
- Multilingual unit tests, randomized differential checks against the reference
  implementation, and two reproducible benchmarks (`benchmark.py`, `shape_matrix.py`).
