import time

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.schemas.search import SearchRequest, SearchResponse, SearchResultOut, SnippetOut
from app.services import cache
from app.services.retrieval import SearchFilters, hybrid_search

router = APIRouter(tags=["search"])


@router.post("/search", response_model=SearchResponse)
async def search(payload: SearchRequest, db: AsyncSession = Depends(get_db)) -> SearchResponse:
    cache_params = {
        "top_k": payload.top_k,
        "filters": payload.filters.model_dump(),
    }
    cached = cache.get(payload.query, cache_params)
    if cached:
        return SearchResponse(**cached, cached=True)

    start = time.perf_counter()
    filters = SearchFilters(
        file_types=payload.filters.file_types,
        directory_prefix=payload.filters.directory_prefix,
        source_types=payload.filters.source_types,
        include_archived=payload.filters.include_archived,
    )
    results = await hybrid_search(db, payload.query, filters, rerank_n=payload.top_k)
    elapsed_ms = (time.perf_counter() - start) * 1000

    out = SearchResponse(
        query=payload.query,
        cached=False,
        elapsed_ms=round(elapsed_ms, 2),
        total=len(results),
        results=[
            SearchResultOut(
                file_id=r.file_id,
                filename=r.filename,
                file_type=r.file_type,
                source_type=r.source_type,
                title=r.title,
                file_path=r.file_path,
                source_path=r.source_path,
                directory_hierarchy=r.directory_hierarchy,
                youtube_url=r.youtube_url,
                score=r.score,
                snippets=[SnippetOut(**s.__dict__) for s in r.snippets],
            )
            for r in results
        ],
    )

    cache.set(payload.query, cache_params, out.model_dump(mode="json", exclude={"cached"}))
    return out
