"""Semantic chunking via LlamaIndex SemanticSplitterNodeParser (FR-010, FR-023, FR-031)."""
from __future__ import annotations

from dataclasses import dataclass
from threading import Lock

from loguru import logger

from app.config import get_settings

_settings = get_settings()
_splitter = None
_lock = Lock()


@dataclass(slots=True)
class TextChunk:
    text: str
    start_char: int
    end_char: int


def _get_splitter():
    global _splitter
    if _splitter is None:
        with _lock:
            if _splitter is None:
                from llama_index.core.node_parser import SemanticSplitterNodeParser
                from llama_index.embeddings.huggingface import HuggingFaceEmbedding

                logger.info("Initializing semantic splitter")
                embed_model = HuggingFaceEmbedding(model_name=_settings.embedding_model)
                _splitter = SemanticSplitterNodeParser(
                    buffer_size=_settings.chunk_buffer_size,
                    breakpoint_percentile_threshold=_settings.chunk_breakpoint_percentile,
                    embed_model=embed_model,
                )
    return _splitter


def _fixed_window_fallback(text: str, size: int = 800, overlap: int = 100) -> list[TextChunk]:
    """Used when text is too short or semantic split produces empty output."""
    chunks: list[TextChunk] = []
    n = len(text)
    start = 0
    step = max(1, size - overlap)
    while start < n:
        end = min(n, start + size)
        chunks.append(TextChunk(text=text[start:end], start_char=start, end_char=end))
        if end == n:
            break
        start += step
    return chunks


def semantic_chunk(text: str) -> list[TextChunk]:
    text = (text or "").strip()
    if not text:
        return []

    # Skip heavy semantic chunking for very short docs
    if len(text) < 1200:
        return _fixed_window_fallback(text, size=800, overlap=100)

    try:
        from llama_index.core import Document

        splitter = _get_splitter()
        nodes = splitter.get_nodes_from_documents([Document(text=text)])
        chunks: list[TextChunk] = []
        for node in nodes:
            chunk_text = node.get_content().strip()
            if not chunk_text:
                continue
            start = text.find(chunk_text)
            if start == -1:
                start = 0
            chunks.append(
                TextChunk(text=chunk_text, start_char=start, end_char=start + len(chunk_text))
            )
        if chunks:
            return chunks
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Semantic chunking failed, falling back to fixed-window: {exc}")

    return _fixed_window_fallback(text)
