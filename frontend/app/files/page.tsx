"use client";

import { useQuery } from "@tanstack/react-query";
import { FileText, Loader2 } from "lucide-react";
import { useState } from "react";

import { api } from "@/lib/api";
import type { FileOut, FileStatus, SourceType } from "@/lib/types";
import { Select } from "@/components/ui/select";
import { StatusBadge } from "@/components/ui/status-badge";
import { Badge } from "@/components/ui/badge";
import { FileActions } from "@/components/files/file-actions";
import { FileDetailDrawer } from "@/components/files/file-detail-drawer";
import { formatBytes, formatDate } from "@/lib/utils";

export default function FilesPage() {
  const [statusFilter, setStatusFilter] = useState<FileStatus | "">("");
  const [sourceFilter, setSourceFilter] = useState<SourceType | "">("");
  const [page, setPage] = useState(0);
  const [selected, setSelected] = useState<FileOut | null>(null);
  const limit = 25;

  const { data, isLoading, isError } = useQuery({
    queryKey: ["files", { statusFilter, sourceFilter, page }],
    queryFn: () =>
      api.listFiles({
        limit,
        offset: page * limit,
        file_status: statusFilter || undefined,
        source_type: sourceFilter || undefined,
      }),
    refetchInterval: (q) => {
      const items = (q.state.data as { items?: FileOut[] } | undefined)?.items || [];
      return items.some((f) => f.status === "pending" || f.status === "processing")
        ? 3000
        : false;
    },
  });

  const totalPages = data ? Math.ceil(data.total / limit) : 0;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-end gap-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Status</label>
          <Select
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value as FileStatus | "");
              setPage(0);
            }}
            className="mt-1 w-44"
          >
            <option value="">All statuses</option>
            <option value="pending">Pending</option>
            <option value="processing">Processing</option>
            <option value="indexed">Indexed</option>
            <option value="failed">Failed</option>
            <option value="archived">Archived</option>
          </Select>
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">Source</label>
          <Select
            value={sourceFilter}
            onChange={(e) => {
              setSourceFilter(e.target.value as SourceType | "");
              setPage(0);
            }}
            className="mt-1 w-44"
          >
            <option value="">All sources</option>
            <option value="upload">Upload</option>
            <option value="directory">Directory</option>
            <option value="external_drive">External drive</option>
            <option value="youtube">YouTube</option>
          </Select>
        </div>
        <div className="ml-auto text-sm text-muted-foreground">
          {data ? `${data.total} file${data.total === 1 ? "" : "s"}` : ""}
        </div>
      </div>

      <div className="rounded-lg border border-border bg-card overflow-hidden">
        <table className="w-full text-sm">
          <thead className="bg-muted/40 text-xs uppercase tracking-wide text-muted-foreground">
            <tr>
              <th className="text-left font-medium px-4 py-2">File</th>
              <th className="text-left font-medium px-4 py-2">Type</th>
              <th className="text-left font-medium px-4 py-2">Status</th>
              <th className="text-left font-medium px-4 py-2">Size</th>
              <th className="text-left font-medium px-4 py-2">Uploaded</th>
              <th className="text-right font-medium px-4 py-2">Actions</th>
            </tr>
          </thead>
          <tbody>
            {isLoading && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  <Loader2 className="mx-auto h-5 w-5 animate-spin" />
                </td>
              </tr>
            )}
            {isError && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-destructive">
                  Failed to load files
                </td>
              </tr>
            )}
            {data?.items.length === 0 && (
              <tr>
                <td colSpan={6} className="px-4 py-8 text-center text-muted-foreground">
                  No files yet. Head to the Ingest tab to add some.
                </td>
              </tr>
            )}
            {data?.items.map((f) => (
              <tr
                key={f.id}
                className="border-t border-border hover:bg-muted/30 cursor-pointer"
                onClick={(e) => {
                  if ((e.target as HTMLElement).closest("button")) return;
                  setSelected(f);
                }}
              >
                <td className="px-4 py-2.5">
                  <div className="flex items-center gap-2 min-w-0">
                    <FileText className="h-4 w-4 shrink-0 text-muted-foreground" />
                    <span className="truncate" title={f.filename}>
                      {f.filename}
                    </span>
                  </div>
                </td>
                <td className="px-4 py-2.5">
                  <Badge variant="outline">.{f.file_type}</Badge>
                </td>
                <td className="px-4 py-2.5">
                  <StatusBadge status={f.status} />
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {formatBytes(f.size_bytes)}
                </td>
                <td className="px-4 py-2.5 text-muted-foreground">
                  {formatDate(f.uploaded_at)}
                </td>
                <td className="px-4 py-2.5 text-right">
                  <FileActions file={f} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {totalPages > 1 && (
        <div className="flex items-center justify-end gap-2 text-sm">
          <button
            disabled={page === 0}
            onClick={() => setPage((p) => Math.max(0, p - 1))}
            className="rounded-md border border-border px-3 py-1 disabled:opacity-50"
          >
            Previous
          </button>
          <span className="text-muted-foreground">
            Page {page + 1} of {totalPages}
          </span>
          <button
            disabled={page + 1 >= totalPages}
            onClick={() => setPage((p) => p + 1)}
            className="rounded-md border border-border px-3 py-1 disabled:opacity-50"
          >
            Next
          </button>
        </div>
      )}

      <FileDetailDrawer file={selected} onClose={() => setSelected(null)} />
    </div>
  );
}
