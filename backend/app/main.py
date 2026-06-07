from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from loguru import logger

from app.api import files, health, ingest, search, upload, youtube
from app.config import get_settings
from app.core.logging import configure_logging
from app.core.middleware import LatencyMiddleware
from app.database import init_db
from app.services import bm25_store, vector_store


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    settings = get_settings()
    logger.info(f"Starting DocuMind backend in {settings.app_env} mode")
    await init_db()
    logger.info("Database initialized")

    # Best-effort: prepare downstream stores. Don't fail startup if unreachable.
    for label, fn in (
        ("Qdrant", vector_store.ensure_collection),
        ("OpenSearch", bm25_store.ensure_index),
    ):
        try:
            fn()
            logger.info(f"{label} ready")
        except Exception as exc:  # noqa: BLE001
            logger.warning(f"{label} not reachable on startup: {exc}")

    yield
    logger.info("Shutting down")


def create_app() -> FastAPI:
    app = FastAPI(
        title="DocuMind API",
        description="AI-Powered Contextual Document Finder",
        version="0.1.0",
        lifespan=lifespan,
    )

    app.add_middleware(LatencyMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(health.router)
    app.include_router(upload.router)
    app.include_router(ingest.router)
    app.include_router(youtube.router)
    app.include_router(search.router)
    app.include_router(files.router)

    return app


app = create_app()
