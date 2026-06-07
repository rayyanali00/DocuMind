"""Sentence-transformer embedding singleton (BAAI/bge-large-en-v1.5)."""
from __future__ import annotations

from threading import Lock

import numpy as np
from loguru import logger

from app.config import get_settings

_settings = get_settings()
_model = None
_lock = Lock()


def get_embedder():
    global _model
    if _model is None:
        with _lock:
            if _model is None:
                from sentence_transformers import SentenceTransformer

                logger.info(f"Loading embedding model: {_settings.embedding_model}")
                _model = SentenceTransformer(_settings.embedding_model)
    return _model


def embed_passages(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.zeros((0, _settings.embedding_dim), dtype=np.float32)
    model = get_embedder()
    return model.encode(
        texts,
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
        batch_size=16,
    )


def embed_query(text: str) -> np.ndarray:
    # bge models recommend a query prefix for instruction-tuned retrieval
    prefixed = f"Represent this sentence for searching relevant passages: {text}"
    model = get_embedder()
    vec = model.encode(
        [prefixed],
        normalize_embeddings=True,
        convert_to_numpy=True,
        show_progress_bar=False,
    )[0]
    return vec
