from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.database import get_db
from app.models.file import FileStatus
from app.pipelines.validators import (
    RejectedFileError,
    UnsupportedFileError,
    validate_upload,
)
from app.schemas.file import FileListResponse, FileOut, UploadResponse
from app.services import file_service
from app.workers.tasks import ingest_file

router = APIRouter(tags=["files"])
settings = get_settings()


@router.post("/upload", response_model=UploadResponse, status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    external_drive_ref: str | None = Form(default=None),
    db: AsyncSession = Depends(get_db),
) -> UploadResponse:
    # We don't know the size until we read; trust Content-Length header if present.
    size_hint = int(file.size or 0)
    try:
        validate_upload(
            filename=file.filename or "",
            size_bytes=size_hint or 1,  # allow 0/unknown; real check happens on disk
            max_size_bytes=settings.max_upload_size_bytes,
        )
    except UnsupportedFileError as exc:
        raise HTTPException(status_code=415, detail=str(exc)) from exc
    except RejectedFileError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_row = await file_service.persist_upload_stream(
        db,
        filename=file.filename or "upload",
        source_stream=file,
        external_drive_ref=external_drive_ref,
    )

    # Re-check size now that we've written to disk
    if file_row.size_bytes > settings.max_upload_size_bytes:
        # Clean up oversized file; flagged for failure
        await file_service.mark_failed(db, file_row.id, "File exceeds max upload size")
        raise HTTPException(status_code=400, detail="File exceeds max upload size")

    task = ingest_file.delay(file_row.id)
    return UploadResponse(file=FileOut.model_validate(file_row), task_id=task.id)


@router.get("/files", response_model=FileListResponse)
async def list_files(
    limit: int = 50,
    offset: int = 0,
    file_status: FileStatus | None = None,
    db: AsyncSession = Depends(get_db),
) -> FileListResponse:
    total, rows = await file_service.list_files(
        db, limit=limit, offset=offset, status=file_status
    )
    return FileListResponse(
        total=total,
        items=[FileOut.model_validate(r) for r in rows],
    )
