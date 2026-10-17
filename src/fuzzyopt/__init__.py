"""Multilingual Fuzzy Search Optimizer."""
from .distance import levenshtein, levenshtein_bounded
from .index import FuzzySearchIndex, Match, normalize

__all__ = [
    "FuzzySearchIndex",
    "Match",
    "levenshtein",
    "levenshtein_bounded",
    "normalize",
]
__version__ = "0.1.0"
