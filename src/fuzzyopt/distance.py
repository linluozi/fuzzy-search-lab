"""Levenshtein distance implementations: reference and threshold-aware."""
from __future__ import annotations


def levenshtein(a: str, b: str) -> int:
    """Return the exact Levenshtein edit distance in O(len(a) * len(b)) time.

    This straightforward dynamic-programming implementation is deliberately
    retained as a correctness oracle and baseline for benchmarks.
    """
    if a == b:
        return 0
    if not a:
        return len(b)
    if not b:
        return len(a)

    # Keep the DP row as short as possible.
    if len(a) > len(b):
        a, b = b, a

    previous = list(range(len(a) + 1))
    for i, char_b in enumerate(b, start=1):
        current = [i] + [0] * len(a)
        for j, char_a in enumerate(a, start=1):
            substitution = 0 if char_a == char_b else 1
            current[j] = min(
                previous[j] + 1,       # deletion
                current[j - 1] + 1,    # insertion
                previous[j - 1] + substitution,
            )
        previous = current
    return previous[-1]


def levenshtein_bounded(a: str, b: str, max_distance: int) -> int:
    """Return exact distance if <= max_distance, otherwise max_distance + 1.

    Optimizations:
    * Reject pairs whose lengths already differ too much.
    * Compute only the diagonal band that could still meet the threshold.
    * Stop when every reachable cell in a row exceeds the threshold.
    * Fall back to the plain row DP once the band covers most of the matrix.

    For small thresholds this visits far fewer DP cells than the reference
    implementation. Strings are compared as Python Unicode code points.
    """
    if not isinstance(max_distance, int) or isinstance(max_distance, bool):
        raise TypeError("max_distance must be a non-negative integer")
    if max_distance < 0:
        raise ValueError("max_distance must be a non-negative integer")

    cutoff = max_distance + 1
    if a == b:
        return 0
    if abs(len(a) - len(b)) > max_distance:
        return cutoff
    if not a:
        return len(b) if len(b) <= max_distance else cutoff
    if not b:
        return len(a) if len(a) <= max_distance else cutoff

    # Use the shorter string as the DP column axis.
    if len(a) > len(b):
        a, b = b, a
    n = len(a)
    m = len(b)
    k = max_distance

    # When the band can cover every column of the shorter string, the per-row
    # boundary checks and the extra list allocation cost more than the cells
    # they save. This is the common case for short strings (e.g. three-character
    # CJK names with k=2).
    if 2 * k + 1 >= n:
        exact = levenshtein(a, b)
        return exact if exact <= k else cutoff

    # Cells outside the band are not reachable within k edits.
    previous = [cutoff] * (n + 1)
    for j in range(0, min(n, k) + 1):
        previous[j] = j

    for i, char_b in enumerate(b, start=1):
        current = [cutoff] * (n + 1)
        if i <= k:
            current[0] = i
        start = max(1, i - k)
        end = min(n, i + k)
        row_min = current[0] if i <= k else cutoff

        for j in range(start, end + 1):
            substitution = 0 if a[j - 1] == char_b else 1
            value = min(
                previous[j] + 1,
                current[j - 1] + 1,
                previous[j - 1] + substitution,
            )
            # Saturate values outside our threshold to avoid needless growth.
            if value > cutoff:
                value = cutoff
            current[j] = value
            if value < row_min:
                row_min = value

        # Edit distance to any prefix has a non-decreasing row minimum.
        if row_min > k:
            return cutoff
        previous = current

    result = previous[n]
    return result if result <= k else cutoff
