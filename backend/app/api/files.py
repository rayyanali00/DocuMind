"""Archive / unarchive / reindex / delete (FR-055..FR-058)."""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.models.file import File, SourceType
from app.schemas.file import FileOut
from app.services import bm25_store, cache, file_service
from app.workers.tasks import ingest_file, ingest_youtube, purge_file

router = APIRouter(tags=["files"])


@router.post("/archive/{file_id}", response_model=FileOut)
async def archive(file_id: str, db: AsyncSession = Depends(get_db)) -> FileOut:
    file_row = await file_service.archive_file(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        bm25_store.update_status(file_id, "archived")
    except Exception:  # noqa: BLE001
        pass
    cache.invalidate_all()
    return FileOut.model_validate(file_row)


@router.post("/unarchive/{file_id}", response_model=FileOut)
async def unarchive(file_id: str, db: AsyncSession = Depends(get_db)) -> FileOut:
    file_row = await file_service.unarchive_file(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    try:
        bm25_store.update_status(file_id, "indexed")
    except Exception:  # noqa: BLE001
        pass
    cache.invalidate_all()
    return FileOut.model_validate(file_row)


@router.post("/reindex/{file_id}")
async def reindex(file_id: str, db: AsyncSession = Depends(get_db)) -> dict:
    file_row = await db.get(File, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")
    if file_row.source_type == SourceType.YOUTUBE:
        task = ingest_youtube.delay(file_id)
    else:
        task = ingest_file.delay(file_id)
    return {"file_id": file_id, "task_id": task.id, "message": "Reindex queued"}


@router.delete("/file/{file_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_file(file_id: str, db: AsyncSession = Depends(get_db)) -> None:
    file_row = await file_service.delete_file_row(db, file_id)
    if file_row is None:
        raise HTTPException(status_code=404, detail="File not found")

    # Best-effort cleanup of on-disk blob (only for non-YouTube sources)
    if file_row.source_type != SourceType.YOUTUBE:
        try:
            p = Path(file_row.file_path)
            if p.exists() and p.is_file():
                p.unlink()
        except Exception:  # noqa: BLE001
            pass

    purge_file.delay(file_id)
    cache.invalidate_all()
