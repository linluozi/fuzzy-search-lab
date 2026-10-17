"""Small dependency-free fuzzy-search index with threshold-aware matching."""
from __future__ import annotations

import heapq
import unicodedata
from dataclasses import dataclass
from typing import Iterable, Optional

from .distance import levenshtein, levenshtein_bounded


def normalize(text: str, *, compatibility: bool = False) -> str:
    """Normalize canonically equivalent Unicode text and case-fold it.

    With ``compatibility=False`` (the default) the text is normalized to NFC,
    which only merges canonically equivalent sequences such as ``e`` + U+0301
    and ``é``. With ``compatibility=True`` it is normalized to NFKC instead,
    which additionally folds full-width forms (``ＡＢＣ`` -> ``ABC``,
    ``ｶﾀｶﾅ`` -> ``カタカナ``), ligatures (``ﬁ`` -> ``fi``) and other
    compatibility characters (``①`` -> ``1``, ``㈱`` -> ``(株)``).

    Compatibility folding is opt-in because it merges characters that a caller
    may consider distinct. Accents and scripts are never transliterated, so
    normalization does not silently merge words that remain different.
    """
    if not isinstance(text, str):
        raise TypeError("search values must be strings")
    form = "NFKC" if compatibility else "NFC"
    return unicodedata.normalize(form, unicodedata.normalize(form, text).casefold())


@dataclass(frozen=True, slots=True)
class Match:
    """A result item. `index` is the item's original position in the input."""
    value: str
    distance: int
    similarity: float
    index: int


class FuzzySearchIndex:
    """An immutable index for repeated fuzzy searches over string values.

    It groups entries by normalized string length. For a query and threshold k,
    only buckets with lengths in [len(query)-k, len(query)+k] are examined.
    Each remaining comparison uses banded, early-exit Levenshtein distance.

    Length bucketing only pays off when the corpus has varied lengths: if every
    value is within ±k characters of the query, the bucket loop degenerates to a
    full scan plus per-bucket overhead. See ``benchmarks/shape_matrix.py`` for
    measurements across corpus shapes.

    Pass ``compatibility=True`` to fold full-width and other compatibility
    characters as well; see :func:`normalize`.
    """

    def __init__(self, values: Iterable[str], *, compatibility: bool = False):
        if isinstance(values, str):
            raise TypeError(
                "values must be an iterable of strings, not a single string"
            )
        if not isinstance(compatibility, bool):
            raise TypeError("compatibility must be a bool")

        self._compatibility = compatibility
        self._values: list[str] = []
        self._normalized: list[str] = []
        self._by_length: dict[int, list[int]] = {}
        for value in values:
            if not isinstance(value, str):
                raise TypeError("all indexed values must be strings")
            index = len(self._values)
            normalized = normalize(value, compatibility=compatibility)
            self._values.append(value)
            self._normalized.append(normalized)
            self._by_length.setdefault(len(normalized), []).append(index)

    def __len__(self) -> int:
        return len(self._values)

    def search(
        self,
        query: str,
        *,
        max_distance: int = 2,
        limit: Optional[int] = 10,
    ) -> list[Match]:
        """Find nearest items at edit distance <= max_distance.

        Results are ordered by edit distance and then original input order for
        deterministic ties. `limit=None` returns every match.
        """
        if not isinstance(max_distance, int) or isinstance(max_distance, bool):
            raise TypeError("max_distance must be a non-negative integer")
        if max_distance < 0:
            raise ValueError("max_distance must be a non-negative integer")

        normalized_query = normalize(query, compatibility=self._compatibility)
        query_length = len(normalized_query)

        if limit is not None:
            if not isinstance(limit, int) or isinstance(limit, bool):
                raise TypeError("limit must be a non-negative integer or None")
            if limit < 0:
                raise ValueError("limit must be a non-negative integer or None")
            if limit == 0:
                return []

        lower = max(0, query_length - max_distance)
        upper = query_length + max_distance
        scored: list[tuple[int, int]] = []

        # Iterate over the lengths that actually exist. Walking the numeric
        # range instead would cost O(max_distance) for large thresholds.
        lengths = [length for length in self._by_length if lower <= length <= upper]
        total = len(self._values)
        scanned = sum(len(self._by_length[length]) for length in lengths)

        # For short strings the band covers the whole matrix, so the bounded
        # variant only adds per-pair overhead. Decide once per query instead of
        # once per candidate.
        use_plain_dp = bool(lengths) and 2 * max_distance + 1 >= min(
            query_length, min(lengths)
        )

        normalized = self._normalized
        if scanned == total:
            # Every entry is a candidate anyway (short strings, clustered
            # lengths). Walking buckets would only add indirection.
            buckets = (range(total),)
        else:
            buckets = (self._by_length[length] for length in lengths)

        # The two loops differ only in the distance function; keeping them
        # separate avoids a per-pair call through a wrapper.
        append = scored.append
        plain = levenshtein
        bounded = levenshtein_bounded
        if use_plain_dp:
            for bucket in buckets:
                for index in bucket:
                    distance = plain(normalized_query, normalized[index])
                    if distance <= max_distance:
                        append((distance, index))
        else:
            for bucket in buckets:
                for index in bucket:
                    distance = bounded(normalized_query, normalized[index], max_distance)
                    if distance <= max_distance:
                        append((distance, index))

        if limit is None:
            scored.sort()
            chosen = scored
        else:
            # A bounded heap avoids sorting and materialising every match when
            # the caller only asked for the first few.
            chosen = heapq.nsmallest(limit, scored)

        return [
            Match(
                self._values[index],
                distance,
                1.0 - distance / max(query_length, len(normalized[index]), 1),
                index,
            )
            for distance, index in chosen
        ]
