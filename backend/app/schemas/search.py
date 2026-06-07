from datetime import datetime

from pydantic import BaseModel, Field


class SearchFiltersIn(BaseModel):
    file_types: list[str] | None = Field(default=None, description="Extensions, e.g. ['pdf']")
    directory_prefix: str | None = None
    source_types: list[str] | None = Field(
        default=None, description="upload | directory | external_drive | youtube"
    )
    include_archived: bool = False


class SearchRequest(BaseModel):
    query: str = Field(..., min_length=1, max_length=1000)
    top_k: int | None = Field(default=None, ge=1, le=50)
    filters: SearchFiltersIn = Field(default_factory=SearchFiltersIn)


class SnippetOut(BaseModel):
    chunk_id: str
    text: str
    highlighted: str
    score: float
    chunk_index: int
    start_seconds: float | None = None
    end_seconds: float | None = None


class SearchResultOut(BaseModel):
    file_id: str
    filename: str
    file_type: str
    source_type: str
    title: str | None
    file_path: str | None
    source_path: str | None
    directory_hierarchy: str | None
    youtube_url: str | None
    score: float
    snippets: list[SnippetOut]


class SearchResponse(BaseModel):
    query: str
    cached: bool = False
    elapsed_ms: float
    total: int
    results: list[SearchResultOut]
    timestamp: datetime = Field(default_factory=datetime.utcnow)
