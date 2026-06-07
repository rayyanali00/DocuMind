from pydantic import BaseModel, Field

from app.schemas.file import FileOut


class YouTubeIndexRequest(BaseModel):
    url: str = Field(..., description="Public YouTube video URL")


class YouTubeIndexResponse(BaseModel):
    file: FileOut
    task_id: str | None = None
    message: str = "YouTube video accepted for transcript ingestion"
