"use client";

import { FileText, Youtube, ExternalLink, Folder } from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Highlighted } from "./highlighted";
import { formatTimestamp } from "@/lib/utils";
import type { SearchResult } from "@/lib/types";

function iconFor(sourceType: string) {
  if (sourceType === "youtube") return Youtube;
  return FileText;
}

function youtubeLinkWithTime(url: string, startSeconds: number | null): string {
  if (startSeconds == null) return url;
  const sep = url.includes("?") ? "&" : "?";
  return `${url}${sep}t=${Math.floor(startSeconds)}s`;
}

export function ResultCard({ result }: { result: SearchResult }) {
  const Icon = iconFor(result.source_type);
  return (
    <article className="rounded-lg border border-border bg-card p-4 shadow-sm hover:shadow transition-shadow">
      <header className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Icon className="h-4 w-4 shrink-0 text-muted-foreground" />
            <h3 className="font-semibold truncate">{result.title || result.filename}</h3>
            <Badge variant="outline" className="shrink-0">
              .{result.file_type}
            </Badge>
          </div>
          {result.directory_hierarchy && (
            <div className="flex items-center gap-1 text-xs text-muted-foreground truncate">
              <Folder className="h-3 w-3 shrink-0" />
              <span className="truncate">{result.directory_hierarchy}</span>
            </div>
          )}
        </div>
        <div className="text-right shrink-0">
          <div className="text-xs text-muted-foreground">score</div>
          <div className="font-mono text-sm">{result.score.toFixed(3)}</div>
        </div>
      </header>

      <ul className="mt-3 space-y-2">
        {result.snippets.map((s) => (
          <li
            key={s.chunk_id}
            className="rounded-md bg-muted/50 p-3 text-sm leading-relaxed"
          >
            <div className="text-foreground">
              <Highlighted html={s.highlighted} />
            </div>
            {s.start_seconds != null && (
              <div className="mt-1 text-xs text-muted-foreground">
                ⏱ {formatTimestamp(s.start_seconds)}
                {s.end_seconds != null ? ` – ${formatTimestamp(s.end_seconds)}` : ""}
              </div>
            )}
          </li>
        ))}
      </ul>

      <footer className="mt-3 flex flex-wrap items-center gap-3 text-xs text-muted-foreground">
        {result.source_type === "youtube" && result.youtube_url ? (
          <a
            href={youtubeLinkWithTime(
              result.youtube_url,
              result.snippets[0]?.start_seconds ?? null
            )}
            target="_blank"
            rel="noopener noreferrer"
            className="inline-flex items-center gap-1 text-accent hover:underline"
          >
            Open on YouTube <ExternalLink className="h-3 w-3" />
          </a>
        ) : result.source_path ? (
          <span className="truncate max-w-md font-mono" title={result.source_path}>
            {result.source_path}
          </span>
        ) : null}
        <span className="ml-auto">{result.snippets.length} snippet{result.snippets.length === 1 ? "" : "s"}</span>
      </footer>
    </article>
  );
}
