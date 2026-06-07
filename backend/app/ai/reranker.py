"""Cross-encoder reranker singleton (BAAI/bge-reranker-large) — FR-042."""
from __future__ import annotations

from threading import Lock

from loguru import logger

from app.config import get_settings

_settings = get_settings()
_model = None
_lock = Lock()


def get_reranker():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import CrossEncoder

                logger.info(f"Loading reranker: {_settings.reranker_model}")
                _model = CrossEncoder(_settings.reranker_model)
    return _model


def rerank(query: str, passages: list[str]) -> list[float]:
    if not passages:
        return []
    model = get_reranker()
    pairs = [(query, p) for p in passages]
    scores = model.predict(pairs, show_progress_bar=False, batch_size=16)
    return [float(s) for s in scores]
