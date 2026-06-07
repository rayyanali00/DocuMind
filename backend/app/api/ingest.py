from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.file import DirectoryIngestRequest, DirectoryIngestResponse
from app.services import file_service
from app.services.scanner import scan_directory
from app.workers.tasks import ingest_file

router = APIRouter(tags=["ingest"])


@router.post("/ingest/directory", response_model=DirectoryIngestResponse)
async def ingest_directory(
    payload: DirectoryIngestRequest,
    db: AsyncSession = Depends(get_db),
) -> DirectoryIngestResponse:
    root = Path(payload.directory).expanduser().resolve()
    if not root.exists() or not root.is_dir():
        raise HTTPException(status_code=400, detail=f"Not a directory: {root}")

    discovered = 0
    accepted = 0
    task_ids: list[str] = []

    for file_path in scan_directory(root):
        discovered += 1
        file_row = await file_service.register_local_file(
            db,
            source_path=file_path,
            root=root,
            external_drive_ref=payload.external_drive_ref,
        )
        if file_row is None:
            continue  # duplicate or unreadable
        accepted += 1
        task = ingest_file.delay(file_row.id)
        task_ids.append(task.id)

    return DirectoryIngestResponse(
        directory=str(root),
        discovered=discovered,
        accepted=accepted,
        skipped=discovered - accepted,
        task_ids=task_ids,
    )
