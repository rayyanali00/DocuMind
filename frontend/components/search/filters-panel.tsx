"use client";

import { Input } from "@/components/ui/input";
import type { SearchFilters, SourceType } from "@/lib/types";

const FILE_TYPES = ["pdf", "docx", "txt", "csv", "xlsx", "pptx", "png", "jpg", "jpeg", "tiff"];
const SOURCE_TYPES: { value: SourceType; label: string }[] = [
  { value: "upload", label: "Upload" },
  { value: "directory", label: "Directory" },
  { value: "external_drive", label: "External drive" },
  { value: "youtube", label: "YouTube" },
];

interface Props {
  value: SearchFilters;
  onChange: (next: SearchFilters) => void;
}

export function FiltersPanel({ value, onChange }: Props) {
  const toggleArray = <T extends string>(arr: T[] | undefined, item: T): T[] | undefined => {
    const set = new Set(arr || []);
    if (set.has(item)) set.delete(item);
    else set.add(item);
    const next = Array.from(set);
    return next.length ? next : undefined;
  };

  return (
    <div className="space-y-5">
      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          File type
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {FILE_TYPES.map((t) => {
            const active = value.file_types?.includes(t);
            return (
              <button
                key={t}
                onClick={() => onChange({ ...value, file_types: toggleArray(value.file_types, t) })}
                className={`rounded-md border px-2 py-1 text-xs transition ${
                  active
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                .{t}
              </button>
            );
          })}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Source
        </h3>
        <div className="flex flex-wrap gap-1.5">
          {SOURCE_TYPES.map(({ value: v, label }) => {
            const active = value.source_types?.includes(v);
            return (
              <button
                key={v}
                onClick={() =>
                  onChange({ ...value, source_types: toggleArray(value.source_types, v) })
                }
                className={`rounded-md border px-2 py-1 text-xs transition ${
                  active
                    ? "border-accent bg-accent text-accent-foreground"
                    : "border-border text-muted-foreground hover:bg-muted"
                }`}
              >
                {label}
              </button>
            );
          })}
        </div>
      </section>

      <section>
        <h3 className="mb-2 text-xs font-semibold uppercase tracking-wide text-muted-foreground">
          Folder prefix
        </h3>
        <Input
          placeholder="e.g. engineering/specs"
          value={value.directory_prefix || ""}
          onChange={(e) =>
            onChange({ ...value, directory_prefix: e.target.value || undefined })
          }
        />
      </section>

      <section>
        <label className="flex items-center gap-2 text-sm">
          <input
            type="checkbox"
            checked={value.include_archived || false}
            onChange={(e) => onChange({ ...value, include_archived: e.target.checked })}
            className="rounded border-border"
          />
          Include archived files
        </label>
      </section>
    </div>
  );
}
