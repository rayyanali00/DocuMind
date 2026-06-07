"""Lightweight metadata extraction (FR-014..FR-018).

We avoid LLM-based extraction (FRD excludes LLM answer synthesis) and use
heuristics: title = first non-empty line, summary = leading text window,
keywords = top TF terms with stopword filtering.
"""
from __future__ import annotations

import re
from collections import Counter
from dataclasses import dataclass

_STOPWORDS = {
    "the", "a", "an", "and", "or", "but", "if", "then", "of", "to", "in", "on",
    "for", "with", "without", "by", "as", "at", "from", "is", "are", "was", "were",
    "be", "been", "being", "this", "that", "these", "those", "it", "its", "i", "you",
    "he", "she", "we", "they", "them", "his", "her", "our", "their", "my", "your",
    "have", "has", "had", "do", "does", "did", "will", "would", "could", "should",
    "may", "might", "can", "shall", "not", "no", "yes", "so", "up", "down", "out",
    "over", "under", "again", "further", "than", "too", "very", "just", "also",
    "into", "through", "about", "against", "between", "during", "before", "after",
    "above", "below", "while", "such", "only", "own", "same", "other", "some", "any",
    "all", "each", "more", "most", "many", "much", "few", "several", "every",
}

_WORD_RE = re.compile(r"[A-Za-z][A-Za-z0-9\-_/]{2,}")


@dataclass(slots=True)
class DocMetadata:
    title: str | None
    summary: str | None
    keywords: list[str]


def extract_title(text: str, fallback: str | None = None) -> str | None:
    for line in (text or "").splitlines():
        s = line.strip()
        if s and len(s) < 200:
            return s
    return fallback


def extract_summary(text: str, max_chars: int = 500) -> str | None:
    s = (text or "").strip()
    if not s:
        return None
    if len(s) <= max_chars:
        return s
    cut = s[:max_chars]
    last_period = cut.rfind(".")
    if last_period > max_chars * 0.6:
        return cut[: last_period + 1]
    return cut + "…"


def extract_keywords(text: str, top_k: int = 10) -> list[str]:
    if not text:
        return []
    tokens = [w.lower() for w in _WORD_RE.findall(text)]
    filtered = [t for t in tokens if t not in _STOPWORDS and len(t) > 2]
    counts = Counter(filtered)
    return [w for w, _ in counts.most_common(top_k)]


def extract_metadata(text: str, fallback_title: str | None = None) -> DocMetadata:
    return DocMetadata(
        title=extract_title(text, fallback=fallback_title),
        summary=extract_summary(text),
        keywords=extract_keywords(text),
    )
