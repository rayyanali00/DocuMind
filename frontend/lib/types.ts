export type FileStatus = "pending" | "processing" | "indexed" | "failed" | "archived";
export type SourceType = "upload" | "directory" | "external_drive" | "youtube";

export interface FileOut {
  id: string;
  filename: string;
  file_type: string;
  mime_type: string | null;
  size_bytes: number;
  source_path: string | null;
  parent_folder: string | null;
  directory_hierarchy: string | null;
  external_drive_ref: string | null;
  status: FileStatus;
  error_message: string | null;
  uploaded_at: string;
  modified_at: string | null;
  indexed_at: string | null;
}

export interface FileListResponse {
  total: number;
  items: FileOut[];
}

export interface UploadResponse {
  file: FileOut;
  task_id: string | null;
  message: string;
}

export interface DirectoryIngestResponse {
  directory: string;
  discovered: number;
  accepted: number;
  skipped: number;
  task_ids: string[];
}

export interface SearchSnippet {
  chunk_id: string;
  text: string;
  highlighted: string;
  score: number;
  chunk_index: number;
  start_seconds: number | null;
  end_seconds: number | null;
}

export interface SearchResult {
  file_id: string;
  filename: string;
  file_type: string;
  source_type: SourceType;
  title: string | null;
  file_path: string | null;
  source_path: string | null;
  directory_hierarchy: string | null;
  youtube_url: string | null;
  score: number;
  snippets: SearchSnippet[];
}

export interface SearchFilters {
  file_types?: string[];
  directory_prefix?: string;
  source_types?: SourceType[];
  include_archived?: boolean;
}

export interface SearchRequest {
  query: string;
  top_k?: number;
  filters?: SearchFilters;
}

export interface SearchResponse {
  query: string;
  cached: boolean;
  elapsed_ms: number;
  total: number;
  results: SearchResult[];
  timestamp: string;
}

export interface HealthResponse {
  status: "ok" | "degraded";
  service: string;
  version: string;
  dependencies: {
    redis: boolean;
    qdrant: boolean;
    opensearch: boolean;
  };
}
