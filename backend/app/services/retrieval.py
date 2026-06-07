"""Hybrid retrieval: vector + BM25 → RRF fusion → cross-encoder rerank (FR-038..FR-051)."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from loguru import logger
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.embeddings import embed_query
from app.ai.reranker import rerank
from app.config import get_settings
from app.models.chunk import Chunk
from app.models.file import File, FileStatus
from app.services import bm25_store, vector_store

_settings = get_settings()


@dataclass(slots=True)
class Snippet:
    chunk_id: str
    text: str
    highlighted: str
    score: float
    chunk_index: int
    start_seconds: float | None = None
    end_seconds: float | None = None


@dataclass(slots=True)
class SearchResult:
    file_id: str
    filename: str
    file_type: str
    source_type: str
    title: str | None
    file_path: str | None
    source_path: str | None
    directory_hierarchy: str | None
    youtube_url: str | None
    score: float
    snippets: list[Snippet] = field(default_factory=list)


@dataclass(slots=True)
class SearchFilters:
    file_types: list[str] | None = None
    directory_prefix: str | None = None
    source_types: list[str] | None = None
    include_archived: bool = False


def _rrf_fuse(
    vector_hits: list[Any],
    bm25_hits: list[Any],
    k: int = 60,
) -> list[tuple[str, float]]:
    """Reciprocal Rank Fusion. Returns [(chunk_id, fused_score), ...] sorted desc."""
    scores: dict[str, float] = {}
    for rank, hit in enumerate(vector_hits, start=1):
        scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank)
    for rank, hit in enumerate(bm25_hits, start=1):
        scores[hit.chunk_id] = scores.get(hit.chunk_id, 0.0) + 1.0 / (k + rank)
    return sorted(scores.items(), key=lambda x: x[1], reverse=True)


def _highlight(text: str, query: str, max_chars: int = 350) -> str:
    """Wrap query terms in <mark>...</mark> and trim to a window around the first match."""
    terms = [t for t in re.findall(r"[A-Za-z0-9]{3,}", query) if t]
    if not terms:
        return text[:max_chars]

    pattern = re.compile(r"(?i)\b(" + "|".join(re.escape(t) for t in terms) + r")\b")
    match = pattern.search(text)
    if match:
        start = max(0, match.start() - max_chars // 2)
        end = min(len(text), start + max_chars)
        snippet = text[start:end]
        prefix = "…" if start > 0 else ""
        suffix = "…" if end < len(text) else ""
        snippet = prefix + snippet + suffix
    else:
        snippet = text[:max_chars] + ("…" if len(text) > max_chars else "")

    return pattern.sub(r"<mark>\1</mark>", snippet)


async def hybrid_search(
    db: AsyncSession,
    query: str,
    filters: SearchFilters,
    *,
    top_k: int | None = None,
    rerank_n: int | None = None,
    max_snippets_per_file: int = 3,
) -> list[SearchResult]:
    """Perform hybrid retrieval and return ranked file results with highlighted snippets."""
    top_k = top_k or _settings.retrieval_top_k
    rerank_n = rerank_n or _settings.rerank_top_n

    exclude_statuses = None if filters.include_archived else [FileStatus.ARCHIVED.value]

    # 1) Vector + BM25 in parallel-ish (sync clients; sequential is fine for now)
    qvec = embed_query(query)
    try:
        vec_hits = vector_store.search(
            qvec,
            top_k=top_k,
            file_types=filters.file_types,
            directory_prefix=filters.directory_prefix,
            source_types=filters.source_types,
            exclude_statuses=exclude_statuses,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Vector search failed: {exc}")
        vec_hits = []

    try:
        bm_hits = bm25_store.search(
            query,
            top_k=top_k,
            file_types=filters.file_types,
            directory_prefix=filters.directory_prefix,
            source_types=filters.source_types,
            exclude_statuses=exclude_statuses,
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"BM25 search failed: {exc}")
        bm_hits = []

    if not vec_hits and not bm_hits:
        return []

    # 2) Fuse and take top candidates for reranking
    fused = _rrf_fuse(vec_hits, bm_hits)
    candidate_ids = [cid for cid, _ in fused[: max(rerank_n * 4, 40)]]
    if not candidate_ids:
        return []

    # 3) Hydrate chunks + file rows from SQL
    chunk_rows = (
        await db.execute(select(Chunk).where(Chunk.id.in_(candidate_ids)))
    ).scalars().all()
    chunks_by_id: dict[str, Chunk] = {c.id: c for c in chunk_rows}

    file_ids = list({c.file_id for c in chunk_rows})
    file_rows = (await db.execute(select(File).where(File.id.in_(file_ids)))).scalars().all()
    files_by_id: dict[str, File] = {f.id: f for f in file_rows}

    # 4) Rerank with cross-encoder
    ordered = [cid for cid in candidate_ids if cid in chunks_by_id]
    passages = [chunks_by_id[cid].text for cid in ordered]
    try:
        rerank_scores = rerank(query, passages)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Reranking failed, falling back to RRF order: {exc}")
        rerank_scores = [1.0 / (i + 1) for i in range(len(ordered))]

    scored = sorted(
        zip(ordered, passages, rerank_scores, strict=True),
        key=lambda x: x[2],
        reverse=True,
    )

    # 5) Group by file, keeping the top-N snippets per file
    grouped: dict[str, SearchResult] = {}
    for chunk_id, text, score in scored:
        chunk = chunks_by_id[chunk_id]
        file_row = files_by_id.get(chunk.file_id)
        if file_row is None:
            continue
        result = grouped.get(file_row.id)
        if result is None:
            result = SearchResult(
                file_id=file_row.id,
                filename=file_row.filename,
                file_type=file_row.file_type,
                source_type=file_row.source_type.value,
                title=file_row.title,
                file_path=file_row.file_path,
                source_path=file_row.source_path,
                directory_hierarchy=file_row.directory_hierarchy,
                youtube_url=file_row.youtube_url,
                score=score,
            )
            grouped[file_row.id] = result
        if len(result.snippets) < max_snippets_per_file:
            result.snippets.append(
                Snippet(
                    chunk_id=chunk.id,
                    text=text,
                    highlighted=_highlight(text, query),
                    score=float(score),
                    chunk_index=chunk.chunk_index,
                    start_seconds=chunk.start_seconds,
                    end_seconds=chunk.end_seconds,
                )
            )

    return sorted(grouped.values(), key=lambda r: r.score, reverse=True)[:rerank_n]
