from fastapi import APIRouter
from pydantic import BaseModel

from app.services import bm25_store, cache, vector_store

router = APIRouter(tags=["health"])


class DependencyStatus(BaseModel):
    redis: bool
    qdrant: bool
    opensearch: bool


class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    dependencies: DependencyStatus


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    deps = DependencyStatus(
        redis=cache.ping(),
        qdrant=vector_store.ping(),
        opensearch=bm25_store.ping(),
    )
    overall = "ok" if all([deps.redis, deps.qdrant, deps.opensearch]) else "degraded"
    return HealthResponse(
        status=overall,
        service="documind-backend",
        version="0.1.0",
        dependencies=deps,
    )
