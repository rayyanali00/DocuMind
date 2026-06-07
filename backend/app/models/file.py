import enum
import uuid
from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Enum, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class FileStatus(str, enum.Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    INDEXED = "indexed"
    FAILED = "failed"
    ARCHIVED = "archived"


class SourceType(str, enum.Enum):
    UPLOAD = "upload"
    DIRECTORY = "directory"
    EXTERNAL_DRIVE = "external_drive"
    YOUTUBE = "youtube"


def _uuid() -> str:
    return str(uuid.uuid4())


class File(Base):
    __tablename__ = "files"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)

    # Identity
    filename: Mapped[str] = mapped_column(String(512), index=True)
    file_path: Mapped[str] = mapped_column(Text)  # stored path on disk (or YouTube URL)
    source_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    parent_folder: Mapped[str | None] = mapped_column(Text, nullable=True)
    directory_hierarchy: Mapped[str | None] = mapped_column(Text, nullable=True)
    external_drive_ref: Mapped[str | None] = mapped_column(String(255), nullable=True)
    source_type: Mapped[SourceType] = mapped_column(
        Enum(SourceType, native_enum=False, length=24),
        default=SourceType.UPLOAD,
        index=True,
    )

    # YouTube-specific
    youtube_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    youtube_video_id: Mapped[str | None] = mapped_column(String(32), nullable=True, index=True)

    # Format
    file_type: Mapped[str] = mapped_column(String(32), index=True)
    mime_type: Mapped[str | None] = mapped_column(String(128), nullable=True)
    size_bytes: Mapped[int] = mapped_column(BigInteger, default=0)
    content_hash: Mapped[str | None] = mapped_column(String(64), index=True, nullable=True)

    # Lifecycle
    status: Mapped[FileStatus] = mapped_column(
        Enum(FileStatus, native_enum=False, length=16),
        default=FileStatus.PENDING,
        index=True,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(default=0)

    # Extraction & metadata
    extracted_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)  # comma-joined
    summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int] = mapped_column(default=0)
    ocr_used: Mapped[bool] = mapped_column(default=False)

    # Timestamps
    uploaded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.utcnow()
    )
    modified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    indexed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
