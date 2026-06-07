"""OpenSearch BM25 store (FR-013, FR-040)."""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock
from typing import Any

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
                from opensearchpy import OpenSearch

                _client = OpenSearch(
                    hosts=[_settings.opensearch_url],
                    http_compress=True,
                    use_ssl=False,
                    verify_certs=False,
                    timeout=30,
                )
    return _client


_INDEX_BODY = {
    "settings": {
        "analysis": {
            "analyzer": {
                "default": {"type": "standard"},
            }
        }
    },
    "mappings": {
        "properties": {
            "file_id": {"type": "keyword"},
            "chunk_id": {"type": "keyword"},
            "chunk_index": {"type": "integer"},
            "text": {"type": "text", "analyzer": "default"},
            "title": {"type": "text"},
            "keywords": {"type": "text"},
            "file_type": {"type": "keyword"},
            "source_type": {"type": "keyword"},
            "status": {"type": "keyword"},
            "directory_hierarchy": {"type": "text"},
            "filename": {"type": "text"},
        }
    },
}


def ensure_index() -> None:
    client = _get_client()
    if not client.indices.exists(index=_settings.opensearch_index):
        logger.info(f"Creating OpenSearch index: {_settings.opensearch_index}")
        client.indices.create(index=_settings.opensearch_index, body=_INDEX_BODY)


def index_chunks(docs: list[dict[str, Any]]) -> None:
    if not docs:
        return
    from opensearchpy.helpers import bulk

    actions = [
        {
            "_op_type": "index",
            "_index": _settings.opensearch_index,
            "_id": d["chunk_id"],
            "_source": d,
        }
        for d in docs
    ]
    bulk(_get_client(), actions, refresh="wait_for")


def delete_by_file(file_id: str) -> None:
    _get_client().delete_by_query(
        index=_settings.opensearch_index,
        body={"query": {"term": {"file_id": file_id}}},
        refresh=True,
    )


@dataclass(slots=True)
class BM25Hit:
    chunk_id: str
    file_id: str
    score: float
    source: dict[str, Any]


def search(
    query: str,
    top_k: int,
    *,
    file_types: list[str] | None = None,
    directory_prefix: str | None = None,
    source_types: list[str] | None = None,
    exclude_statuses: list[str] | None = None,
) -> list[BM25Hit]:
    must: list[dict[str, Any]] = [
        {
            "multi_match": {
                "query": query,
                "fields": ["text^3", "title^2", "keywords^2", "filename"],
            }
        }
    ]
    filters: list[dict[str, Any]] = []
    must_not: list[dict[str, Any]] = []
    if file_types:
        filters.append({"terms": {"file_type": file_types}})
    if source_types:
        filters.append({"terms": {"source_type": source_types}})
    if directory_prefix:
        filters.append({"match_phrase": {"directory_hierarchy": directory_prefix}})
    if exclude_statuses:
        must_not.append({"terms": {"status": exclude_statuses}})

    body = {
        "size": top_k,
        "query": {
            "bool": {
                "must": must,
                "filter": filters,
                "must_not": must_not,
            }
        },
    }
    res = _get_client().search(index=_settings.opensearch_index, body=body)
    hits = res.get("hits", {}).get("hits", [])
    return [
        BM25Hit(
            chunk_id=str(h["_source"].get("chunk_id", h["_id"])),
            file_id=str(h["_source"].get("file_id", "")),
            score=float(h.get("_score", 0.0)),
            source=h["_source"],
        )
        for h in hits
    ]


def update_status(file_id: str, status: str) -> None:
    """Update the status field on all chunks for a file (archive/unarchive)."""
    _get_client().update_by_query(
        index=_settings.opensearch_index,
        body={
            "query": {"term": {"file_id": file_id}},
            "script": {
                "source": "ctx._source.status = params.s",
                "params": {"s": status},
            },
        },
        refresh=True,
    )


def ping() -> bool:
    try:
        return bool(_get_client().ping())
    except Exception:  # noqa: BLE001
        return False
