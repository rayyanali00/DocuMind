from __future__ import annotations

import hashlib
import shutil
import uuid
from datetime import datetime
from pathlib import Path

from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.chunk import Chunk
from app.models.file import File, FileStatus, SourceType
from app.pipelines.validators import get_extension, guess_mime

settings = get_settings()


def _hash_file(path: Path, chunk_size: int = 65536) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(chunk_size):
            h.update(chunk)
    return h.hexdigest()


def _stored_path_for(filename: str) -> Path:
    ext = get_extension(filename)
    unique = f"{uuid.uuid4().hex}.{ext}" if ext else uuid.uuid4().hex
    return settings.upload_dir / unique


async def persist_upload_stream(
    db: AsyncSession,
    *,
    filename: str,
    source_stream,
    source_path: str | None = None,
    external_drive_ref: str | None = None,
    source_type: SourceType = SourceType.UPLOAD,
) -> File:
    dest = _stored_path_for(filename)
    size = 0
    with dest.open("wb") as out:
        while True:
            chunk = await source_stream.read(1024 * 1024)
            if not chunk:
                break
            out.write(chunk)
            size += len(chunk)

    return await _create_file_row(
        db,
        filename=filename,
        stored_path=dest,
        size_bytes=size,
        source_path=source_path,
        external_drive_ref=external_drive_ref,
        source_type=source_type,
    )


async def register_local_file(
    db: AsyncSession,
    *,
    source_path: Path,
    root: Path | None = None,
    external_drive_ref: str | None = None,
    copy_into_storage: bool = True,
) -> File | None:
    if not source_path.exists() or not source_path.is_file():
        return None

    content_hash = _hash_file(source_path)
    existing = await db.scalar(select(File).where(File.content_hash == content_hash))
    if existing is not None:
        return None

    if copy_into_storage:
        dest = _stored_path_for(source_path.name)
        shutil.copy2(source_path, dest)
        stored_path = dest
    else:
        stored_path = source_path

    src_type = SourceType.EXTERNAL_DRIVE if external_drive_ref else SourceType.DIRECTORY
    return await _create_file_row(
        db,
        filename=source_path.name,
        stored_path=stored_path,
        size_bytes=source_path.stat().st_size,
        source_path=str(source_path),
        parent_folder=str(source_path.parent),
        directory_hierarchy=_hierarchy(source_path, root),
        external_drive_ref=external_drive_ref,
        content_hash=content_hash,
        modified_at=datetime.utcfromtimestamp(source_path.stat().st_mtime),
        source_type=src_type,
    )


async def register_youtube(
    db: AsyncSession,
    *,
    url: str,
    video_id: str,
    title: str | None,
) -> File | None:
    existing = await db.scalar(select(File).where(File.youtube_video_id == video_id))
    if existing is not None:
        return None
    file_row = File(
        filename=title or f"YouTube {video_id}",
        file_path=url,
        source_path=url,
        file_type="youtube",
        mime_type="text/vtt",
        source_type=SourceType.YOUTUBE,
        youtube_url=url,
        youtube_video_id=video_id,
        title=title,
        status=FileStatus.PENDING,
    )
    db.add(file_row)
    await db.commit()
    await db.refresh(file_row)
    return file_row


def _hierarchy(path: Path, root: Path | None) -> str:
    if root is not None:
        try:
            return "/".join(path.relative_to(root).parent.parts)
        except ValueError:
            pass
    return "/".join(path.parent.parts)


async def _create_file_row(
    db: AsyncSession,
    *,
    filename: str,
    stored_path: Path,
    size_bytes: int,
    source_path: str | None = None,
    parent_folder: str | None = None,
    directory_hierarchy: str | None = None,
    external_drive_ref: str | None = None,
    content_hash: str | None = None,
    modified_at: datetime | None = None,
    source_type: SourceType = SourceType.UPLOAD,
) -> File:
    file_row = File(
        filename=filename,
        file_path=str(stored_path),
        source_path=source_path,
        parent_folder=parent_folder,
        directory_hierarchy=directory_hierarchy,
        external_drive_ref=external_drive_ref,
        source_type=source_type,
        file_type=get_extension(filename),
        mime_type=guess_mime(filename),
        size_bytes=size_bytes,
        content_hash=content_hash,
        status=FileStatus.PENDING,
        modified_at=modified_at,
    )
    db.add(file_row)
    await db.commit()
    await db.refresh(file_row)
    return file_row


async def mark_processing(db: AsyncSession, file_id: str) -> None:
    file_row = await db.get(File, file_id)
    if file_row is None:
        return
    file_row.status = FileStatus.PROCESSING
    await db.commit()


async def mark_indexed(
    db: AsyncSession,
    file_id: str,
    *,
    extracted_text: str,
    title: str | None,
    summary: str | None,
    keywords: list[str],
    chunk_count: int,
    ocr_used: bool = False,
) -> None:
    file_row = await db.get(File, file_id)
    if file_row is None:
        return
    file_row.status = FileStatus.INDEXED
    file_row.extracted_text = extracted_text
    file_row.title = title or file_row.title
    file_row.summary = summary
    file_row.keywords = ",".join(keywords) if keywords else None
    file_row.chunk_count = chunk_count
    file_row.ocr_used = ocr_used
    file_row.indexed_at = datetime.utcnow()
    file_row.error_message = None
    await db.commit()


async def mark_failed(db: AsyncSession, file_id: str, error: str) -> None:
    file_row = await db.get(File, file_id)
    if file_row is None:
        return
    file_row.status = FileStatus.FAILED
    file_row.error_message = error[:2000]
    file_row.retry_count += 1
    await db.commit()


async def replace_chunks(db: AsyncSession, file_id: str, chunks: list[Chunk]) -> None:
    """Atomically replace all chunks for a file."""
    await db.execute(delete(Chunk).where(Chunk.file_id == file_id))
    for c in chunks:
        db.add(c)
    await db.commit()


async def list_files(
    db: AsyncSession,
    *,
    limit: int = 100,
    offset: int = 0,
    status: FileStatus | None = None,
    source_type: SourceType | None = None,
    include_archived: bool = True,
) -> tuple[int, list[File]]:
    stmt = select(File)
    count_stmt = select(func.count(File.id))
    if status is not None:
        stmt = stmt.where(File.status == status)
        count_stmt = count_stmt.where(File.status == status)
    elif not include_archived:
        stmt = stmt.where(File.status != FileStatus.ARCHIVED)
        count_stmt = count_stmt.where(File.status != FileStatus.ARCHIVED)
    if source_type is not None:
        stmt = stmt.where(File.source_type == source_type)
        count_stmt = count_stmt.where(File.source_type == source_type)

    total = (await db.execute(count_stmt)).scalar_one()
    stmt = stmt.order_by(File.uploaded_at.desc()).limit(limit).offset(offset)
    rows = (await db.execute(stmt)).scalars().all()
    return total, list(rows)


async def archive_file(db: AsyncSession, file_id: str) -> File | None:
    file_row = await db.get(File, file_id)
    if file_row is None:
        return None
    file_row.status = FileStatus.ARCHIVED
    await db.commit()
    return file_row


async def unarchive_file(db: AsyncSession, file_id: str) -> File | None:
    file_row = await db.get(File, file_id)
    if file_row is None or file_row.status != FileStatus.ARCHIVED:
        return file_row
    file_row.status = FileStatus.INDEXED if file_row.chunk_count else FileStatus.PENDING
    await db.commit()
    return file_row


async def delete_file_row(db: AsyncSession, file_id: str) -> File | None:
    file_row = await db.get(File, file_id)
    if file_row is None:
        return None
    await db.delete(file_row)
    await db.commit()
    return file_row
