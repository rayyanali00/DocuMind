"""Celery tasks: full ingestion pipeline (extract → chunk → embed → index)."""
from __future__ import annotations

import asyncio
from pathlib import Path

from celery import shared_task
from loguru import logger

from app.ai.chunker import TextChunk, semantic_chunk
from app.ai.embeddings import embed_passages
from app.ai.metadata_extractor import extract_metadata
from app.database import AsyncSessionLocal
from app.models.chunk import Chunk
from app.models.file import File
from app.pipelines.extractors import ExtractionError, extract_text
from app.services import bm25_store, cache, file_service, vector_store
from app.services.youtube import YouTubeError, fetch_transcript


def _run(coro):
    return asyncio.run(coro)


# ---------- File ingestion ----------

@shared_task(
    bind=True,
    name="documind.ingest_file",
    autoretry_for=(OSError, ConnectionError),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def ingest_file(self, file_id: str) -> dict:
    logger.info(f"[ingest_file] start file_id={file_id}")
    return _run(_ingest_file_async(file_id))


async def _ingest_file_async(file_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        file_row = await db.get(File, file_id)
        if file_row is None:
            return {"file_id": file_id, "status": "not_found"}

        await file_service.mark_processing(db, file_id)

        stored_path = Path(file_row.file_path)
        if not stored_path.exists():
            await file_service.mark_failed(db, file_id, f"Stored file missing: {stored_path}")
            return {"file_id": file_id, "status": "failed", "reason": "missing"}

        try:
            extraction = extract_text(stored_path)
        except ExtractionError as exc:
            logger.error(f"[ingest_file] extraction failed: {exc}")
            await file_service.mark_failed(db, file_id, str(exc))
            return {"file_id": file_id, "status": "failed", "reason": str(exc)}

        text = extraction.text or ""
        if not text.strip():
            await file_service.mark_failed(db, file_id, "No extractable text")
            return {"file_id": file_id, "status": "failed", "reason": "empty_text"}

        text_chunks = semantic_chunk(text)
        if not text_chunks:
            await file_service.mark_failed(db, file_id, "Chunking produced no output")
            return {"file_id": file_id, "status": "failed", "reason": "no_chunks"}

        metadata = extract_metadata(text, fallback_title=file_row.filename)

        await _index_chunks(file_row, text_chunks, metadata, ocr_used=extraction.ocr_used)

        await file_service.mark_indexed(
            db,
            file_id,
            extracted_text=text,
            title=metadata.title,
            summary=metadata.summary,
            keywords=metadata.keywords,
            chunk_count=len(text_chunks),
            ocr_used=extraction.ocr_used,
        )

    cache.invalidate_all()
    logger.info(f"[ingest_file] done file_id={file_id} chunks={len(text_chunks)}")
    return {"file_id": file_id, "status": "indexed", "chunks": len(text_chunks)}


# ---------- YouTube ingestion ----------

@shared_task(
    bind=True,
    name="documind.ingest_youtube",
    autoretry_for=(ConnectionError,),
    retry_backoff=True,
    retry_backoff_max=300,
    max_retries=3,
)
def ingest_youtube(self, file_id: str) -> dict:
    logger.info(f"[ingest_youtube] start file_id={file_id}")
    return _run(_ingest_youtube_async(file_id))


async def _ingest_youtube_async(file_id: str) -> dict:
    async with AsyncSessionLocal() as db:
        file_row = await db.get(File, file_id)
        if file_row is None or not file_row.youtube_url:
            return {"file_id": file_id, "status": "not_found"}

        await file_service.mark_processing(db, file_id)

        try:
            transcript = fetch_transcript(file_row.youtube_url)
        except YouTubeError as exc:
            logger.error(f"[ingest_youtube] {exc}")
            await file_service.mark_failed(db, file_id, str(exc))
            return {"file_id": file_id, "status": "failed", "reason": str(exc)}

        if not transcript.segments:
            await file_service.mark_failed(db, file_id, "No transcript segments")
            return {"file_id": file_id, "status": "failed", "reason": "no_transcript"}

        # Chunk transcript text but preserve per-chunk timestamp ranges
        text_chunks = semantic_chunk(transcript.full_text)
        if not text_chunks:
            await file_service.mark_failed(db, file_id, "Chunking produced no output")
            return {"file_id": file_id, "status": "failed", "reason": "no_chunks"}

        timestamps = _map_timestamps(transcript.segments, text_chunks)
        metadata = extract_metadata(
            transcript.full_text,
            fallback_title=transcript.title or file_row.filename,
        )

        await _index_chunks(
            file_row,
            text_chunks,
            metadata,
            timestamps=timestamps,
            ocr_used=False,
        )

        await file_service.mark_indexed(
            db,
            file_id,
            extracted_text=transcript.full_text,
            title=transcript.title or metadata.title,
            summary=metadata.summary,
            keywords=metadata.keywords,
            chunk_count=len(text_chunks),
            ocr_used=False,
        )

    cache.invalidate_all()
    logger.info(f"[ingest_youtube] done file_id={file_id} chunks={len(text_chunks)}")
    return {"file_id": file_id, "status": "indexed", "chunks": len(text_chunks)}


# ---------- Shared indexing helpers ----------

def _map_timestamps(segments, text_chunks: list[TextChunk]):
    """For each chunk, find segments whose text appears in it; return (start, end) seconds.

    Simple heuristic: walk segments in order, accumulate their text length, and
    map each chunk's char range to the segments overlapping that range.
    """
    seg_offsets: list[tuple[int, int, float, float]] = []  # (start_char, end_char, start_s, end_s)
    cursor = 0
    for seg in segments:
        seg_text = seg.text + "\n"
        start = cursor
        end = cursor + len(seg_text)
        seg_offsets.append((start, end, seg.start, seg.start + seg.duration))
        cursor = end

    result: list[tuple[float | None, float | None]] = []
    for chunk in text_chunks:
        starts = [s for cs, ce, s, _ in seg_offsets if cs < chunk.end_char and ce > chunk.start_char]
        ends = [e for cs, ce, _, e in seg_offsets if cs < chunk.end_char and ce > chunk.start_char]
        result.append((min(starts) if starts else None, max(ends) if ends else None))
    return result


async def _index_chunks(
    file_row: File,
    text_chunks: list[TextChunk],
    metadata,
    *,
    timestamps: list[tuple[float | None, float | None]] | None = None,
    ocr_used: bool = False,
) -> None:
    """Persist chunks to SQL, embed them, and push to Qdrant + OpenSearch."""
    # Ensure stores are initialized
    try:
        vector_store.ensure_collection()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Could not ensure Qdrant collection: {exc}")
        raise
    try:
        bm25_store.ensure_index()
    except Exception as exc:  # noqa: BLE001
        logger.error(f"Could not ensure OpenSearch index: {exc}")
        raise

    # Drop any prior chunks/vectors for this file (idempotent reindex)
    try:
        vector_store.delete_by_file(file_row.id)
    except Exception:  # noqa: BLE001
        pass
    try:
        bm25_store.delete_by_file(file_row.id)
    except Exception:  # noqa: BLE001
        pass

    # Build Chunk rows
    chunk_rows: list[Chunk] = []
    for i, tc in enumerate(text_chunks):
        ts_start, ts_end = (timestamps[i] if timestamps else (None, None))
        chunk_rows.append(
            Chunk(
                file_id=file_row.id,
                chunk_index=i,
                text=tc.text,
                start_char=tc.start_char,
                end_char=tc.end_char,
                start_seconds=ts_start,
                end_seconds=ts_end,
            )
        )

    async with AsyncSessionLocal() as db:
        await file_service.replace_chunks(db, file_row.id, chunk_rows)

    # Embed (sync, batched)
    texts = [c.text for c in chunk_rows]
    vectors = embed_passages(texts)

    # Build payloads for both stores
    base_payload = {
        "file_id": file_row.id,
        "filename": file_row.filename,
        "file_type": file_row.file_type,
        "source_type": file_row.source_type.value,
        "status": "indexed",
        "directory_hierarchy": file_row.directory_hierarchy or "",
        "title": metadata.title or "",
        "keywords": ",".join(metadata.keywords) if metadata.keywords else "",
        "youtube_url": file_row.youtube_url or "",
    }
    vector_payloads = [
        {**base_payload, "chunk_id": c.id, "chunk_index": c.chunk_index} for c in chunk_rows
    ]
    bm25_docs = [
        {
            **base_payload,
            "chunk_id": c.id,
            "chunk_index": c.chunk_index,
            "text": c.text,
        }
        for c in chunk_rows
    ]

    vector_store.upsert_chunks(
        [c.id for c in chunk_rows], vectors, vector_payloads,
    )
    bm25_store.index_chunks(bm25_docs)


# ---------- File lifecycle ----------

@shared_task(name="documind.purge_file")
def purge_file(file_id: str) -> dict:
    """Remove a file from vector + BM25 stores (and on-disk blob if any)."""
    try:
        vector_store.delete_by_file(file_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Qdrant delete failed for {file_id}: {exc}")
    try:
        bm25_store.delete_by_file(file_id)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"OpenSearch delete failed for {file_id}: {exc}")
    cache.invalidate_all()
    return {"file_id": file_id, "status": "purged"}
