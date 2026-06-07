import uuid

from sqlalchemy import ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


def _uuid() -> str:
    return str(uuid.uuid4())


class Chunk(Base):
    __tablename__ = "chunks"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=_uuid)
    file_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("files.id", ondelete="CASCADE"), index=True
    )
    chunk_index: Mapped[int] = mapped_column(Integer)
    text: Mapped[str] = mapped_column(Text)

    # Char offsets in the source document (for highlighting / linking)
    start_char: Mapped[int] = mapped_column(Integer, default=0)
    end_char: Mapped[int] = mapped_column(Integer, default=0)

    # YouTube/transcript timestamp (seconds) if applicable
    start_seconds: Mapped[float | None] = mapped_column(nullable=True)
    end_seconds: Mapped[float | None] = mapped_column(nullable=True)
