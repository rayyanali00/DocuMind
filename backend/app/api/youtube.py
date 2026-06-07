from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.file import FileOut
from app.schemas.youtube import YouTubeIndexRequest, YouTubeIndexResponse
from app.services import file_service
from app.services.youtube import YouTubeError, extract_video_id
from app.workers.tasks import ingest_youtube

router = APIRouter(tags=["youtube"])


@router.post(
    "/youtube/index",
    response_model=YouTubeIndexResponse,
    status_code=status.HTTP_202_ACCEPTED,
)
async def index_youtube(
    payload: YouTubeIndexRequest, db: AsyncSession = Depends(get_db)
) -> YouTubeIndexResponse:
    try:
        video_id = extract_video_id(payload.url)
    except YouTubeError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc

    file_row = await file_service.register_youtube(
        db, url=payload.url, video_id=video_id, title=None
    )
    if file_row is None:
        raise HTTPException(status_code=409, detail="Video already indexed")

    task = ingest_youtube.delay(file_row.id)
    return YouTubeIndexResponse(file=FileOut.model_validate(file_row), task_id=task.id)
