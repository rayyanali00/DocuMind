"""Qdrant vector store wrapper (FR-012)."""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

import numpy as np
from loguru import logger

from app.config import get_settings

_settings = get_settings()
_client = None
_lock = Lock()


def _get_client():
    global _client
    if _client is None:
        with _lock:
            if _client is None:
                from qdrant_client import QdrantClient

                _client = QdrantClient(url=_settings.qdrant_url, timeout=30)
    return _client


def ensure_collection() -> None:
    from qdrant_client.http import models as qm

    client = _get_client()
    existing = {c.name for c in client.get_collections().collections}
    if _settings.qdrant_collection in existing:
        return
    logger.info(f"Creating Qdrant collection: {_settings.qdrant_collection}")
    client.create_collection(
        collection_name=_settings.qdrant_collection,
        vectors_config=qm.VectorParams(size=_settings.embedding_dim, distance=qm.Distance.COSINE),
    )
    # Payload indexes for filtering (FR-046)
    for field in ("file_id", "file_type", "source_type", "status", "directory_hierarchy"):
        try:
            client.create_payload_index(
                collection_name=_settings.qdrant_collection,
                field_name=field,
                field_schema=qm.PayloadSchemaType.KEYWORD,
            )
        except Exception:  # noqa: BLE001 - index may already exist
            pass


def upsert_chunks(
    chunk_ids: list[str],
    vectors: np.ndarray,
    payloads: list[dict[str, Any]],
) -> None:
    if not chunk_ids:
        return
    from qdrant_client.http import models as qm

    client = _get_client()
    points = [
        qm.PointStruct(id=cid, vector=vec.tolist(), payload=payload)
        for cid, vec, payload in zip(chunk_ids, vectors, payloads, strict=True)
    ]
    client.upsert(collection_name=_settings.qdrant_collection, points=points, wait=True)


def delete_by_file(file_id: str) -> None:
    from qdrant_client.http import models as qm

    client = _get_client()
    client.delete(
        collection_name=_settings.qdrant_collection,
        points_selector=qm.FilterSelector(
            filter=qm.Filter(
                must=[qm.FieldCondition(key="file_id", match=qm.MatchValue(value=file_id))]
            )
        ),
        wait=True,
    )


@dataclass(slots=True)
class VectorHit:
    chunk_id: str
    file_id: str
    score: float
    payload: dict[str, Any]


def search(
    vector: np.ndarray,
    top_k: int,
    *,
    file_types: list[str] | None = None,
    directory_prefix: str | None = None,
    source_types: list[str] | None = None,
    exclude_statuses: list[str] | None = None,
) -> list[VectorHit]:
    from qdrant_client.http import models as qm

    must: list[qm.FieldCondition] = []
    must_not: list[qm.FieldCondition] = []
    if file_types:
        must.append(qm.FieldCondition(key="file_type", match=qm.MatchAny(any=file_types)))
    if source_types:
        must.append(qm.FieldCondition(key="source_type", match=qm.MatchAny(any=source_types)))
    if directory_prefix:
        must.append(
            qm.FieldCondition(
                key="directory_hierarchy", match=qm.MatchText(text=directory_prefix)
            )
        )
    if exclude_statuses:
        must_not.append(qm.FieldCondition(key="status", match=qm.MatchAny(any=exclude_statuses)))

    qfilter = qm.Filter(must=must or None, must_not=must_not or None) if (must or must_not) else None

    client = _get_client()
    res = client.search(
        collection_name=_settings.qdrant_collection,
        query_vector=vector.tolist(),
        limit=top_k,
        query_filter=qfilter,
        with_payload=True,
    )
    return [
        VectorHit(
            chunk_id=str(p.id),
            file_id=str(p.payload.get("file_id", "")),
            score=float(p.score),
            payload=dict(p.payload or {}),
        )
        for p in res
    ]


def ping() -> bool:
    try:
        _get_client().get_collections()
        return True
    except Exception:  # noqa: BLE001
        return False
