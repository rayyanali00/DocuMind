"""Latency tracking middleware (NFR-013)."""
from __future__ import annotations

import time

from loguru import logger
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class LatencyMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = (time.perf_counter() - start) * 1000
        response.headers["X-Response-Time-Ms"] = f"{elapsed_ms:.2f}"
        if request.url.path.startswith("/search"):
            logger.info(
                f"search latency path={request.url.path} ms={elapsed_ms:.2f} "
                f"status={response.status_code}"
            )
        return response
