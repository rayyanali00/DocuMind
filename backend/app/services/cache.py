"""Redis-backed query cache (FR-052..FR-054)."""
from __future__ import annotations

import hashlib
import json
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
                import redis

                _client = redis.Redis.from_url(_settings.redis_url, decode_responses=True)
    return _client


def _key(query: str, params: dict[str, Any]) -> str:
    raw = json.dumps({"q": query, "p": params}, sort_keys=True, default=str)
    return "documind:search:" + hashlib.sha256(raw.encode()).hexdigest()


def get(query: str, params: dict[str, Any]) -> dict[str, Any] | None:
    try:
        val = _get_client().get(_key(query, params))
        return json.loads(val) if val else None
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Cache GET failed: {exc}")
        return None


def set(query: str, params: dict[str, Any], value: dict[str, Any]) -> None:
    try:
        _get_client().setex(
            _key(query, params),
            _settings.cache_ttl_seconds,
            json.dumps(value, default=str),
        )
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Cache SET failed: {exc}")


def invalidate_all() -> None:
    try:
        client = _get_client()
        for k in client.scan_iter(match="documind:search:*", count=1000):
            client.delete(k)
    except Exception as exc:  # noqa: BLE001
        logger.warning(f"Cache invalidation failed: {exc}")


def ping() -> bool:
    try:
        return bool(_get_client().ping())
    except Exception:  # noqa: BLE001
        return False
