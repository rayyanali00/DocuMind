from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.file import FileStatus


class FileOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    filename: str
    file_type: str
    mime_type: str | None
    size_bytes: int
    source_path: str | None
    parent_folder: str | None
    directory_hierarchy: str | None
    external_drive_ref: str | None
    status: FileStatus
    error_message: str | None
    uploaded_at: datetime
    modified_at: datetime | None
    indexed_at: datetime | None


class UploadResponse(BaseModel):
    file: FileOut
    task_id: str | None = None
    message: str = "File accepted for ingestion"


class DirectoryIngestRequest(BaseModel):
    directory: str = Field(..., description="Absolute path to the directory to scan recursively")
    external_drive_ref: str | None = Field(
        default=None, description="Optional label/UUID identifying the external drive"
    )


class DirectoryIngestResponse(BaseModel):
    directory: str
    discovered: int
    accepted: int
    skipped: int
    task_ids: list[str]


class FileListResponse(BaseModel):
    total: int
    items: list[FileOut]
