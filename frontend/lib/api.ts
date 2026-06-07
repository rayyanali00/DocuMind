import type {
  DirectoryIngestResponse,
  FileListResponse,
  FileOut,
  FileStatus,
  HealthResponse,
  SearchRequest,
  SearchResponse,
  SourceType,
  UploadResponse,
} from "./types";

const BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

class ApiError extends Error {
  constructor(public status: number, message: string, public detail?: unknown) {
    super(message);
  }
}

async function request<T>(path: string, init: RequestInit = {}): Promise<T> {
  const res = await fetch(`${BASE_URL}${path}`, {
    ...init,
    headers: {
      ...(init.body && !(init.body instanceof FormData) ? { "Content-Type": "application/json" } : {}),
      ...init.headers,
    },
  });

  if (!res.ok) {
    let detail: unknown = undefined;
    try {
      detail = await res.json();
    } catch {
      detail = await res.text();
    }
    const message =
      (detail && typeof detail === "object" && "detail" in detail && String((detail as { detail: unknown }).detail)) ||
      `Request failed with status ${res.status}`;
    throw new ApiError(res.status, message, detail);
  }

  if (res.status === 204) return undefined as T;
  return (await res.json()) as T;
}

export const api = {
  // Health
  health: () => request<HealthResponse>("/health"),

  // Files
  listFiles: (params: {
    limit?: number;
    offset?: number;
    file_status?: FileStatus;
    source_type?: SourceType;
  } = {}) => {
    const qs = new URLSearchParams();
    if (params.limit != null) qs.set("limit", String(params.limit));
    if (params.offset != null) qs.set("offset", String(params.offset));
    if (params.file_status) qs.set("file_status", params.file_status);
    if (params.source_type) qs.set("source_type", params.source_type);
    return request<FileListResponse>(`/files${qs.toString() ? `?${qs}` : ""}`);
  },

  uploadFile: (file: File, externalDriveRef?: string) => {
    const fd = new FormData();
    fd.append("file", file);
    if (externalDriveRef) fd.append("external_drive_ref", externalDriveRef);
    return request<UploadResponse>("/upload", { method: "POST", body: fd });
  },

  ingestDirectory: (directory: string, externalDriveRef?: string) =>
    request<DirectoryIngestResponse>("/ingest/directory", {
      method: "POST",
      body: JSON.stringify({ directory, external_drive_ref: externalDriveRef || null }),
    }),

  indexYoutube: (url: string) =>
    request<UploadResponse>("/youtube/index", {
      method: "POST",
      body: JSON.stringify({ url }),
    }),

  // Search
  search: (payload: SearchRequest) =>
    request<SearchResponse>("/search", { method: "POST", body: JSON.stringify(payload) }),

  // File lifecycle
  archive: (id: string) => request<FileOut>(`/archive/${id}`, { method: "POST" }),
  unarchive: (id: string) => request<FileOut>(`/unarchive/${id}`, { method: "POST" }),
  reindex: (id: string) =>
    request<{ file_id: string; task_id: string; message: string }>(`/reindex/${id}`, { method: "POST" }),
  deleteFile: (id: string) => request<void>(`/file/${id}`, { method: "DELETE" }),
};

export { ApiError };
