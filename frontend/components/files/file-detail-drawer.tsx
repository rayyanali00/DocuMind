"use client";

import { Drawer } from "@/components/ui/drawer";
import { StatusBadge } from "@/components/ui/status-badge";
import { Badge } from "@/components/ui/badge";
import { formatBytes, formatDate } from "@/lib/utils";
import type { FileOut } from "@/lib/types";
import { FileActions } from "./file-actions";

interface Props {
  file: FileOut | null;
  onClose: () => void;
}

export function FileDetailDrawer({ file, onClose }: Props) {
  return (
    <Drawer open={!!file} onClose={onClose} title={file?.filename || ""}>
      {file && (
        <div className="space-y-5 text-sm">
          <div className="flex items-center gap-2 flex-wrap">
            <StatusBadge status={file.status} />
            <Badge variant="outline">.{file.file_type}</Badge>
            <Badge variant="muted">{formatBytes(file.size_bytes)}</Badge>
          </div>

          {file.error_message && (
            <div className="rounded-md border border-destructive/40 bg-destructive/10 p-3 text-destructive">
              <div className="font-semibold text-xs uppercase mb-1">Error</div>
              {file.error_message}
            </div>
          )}

          <Field label="File ID" mono>
            {file.id}
          </Field>
          <Field label="MIME">{file.mime_type || "—"}</Field>
          <Field label="Source path" mono>
            {file.source_path || "—"}
          </Field>
          <Field label="Parent folder" mono>
            {file.parent_folder || "—"}
          </Field>
          <Field label="Directory hierarchy" mono>
            {file.directory_hierarchy || "—"}
          </Field>
          {file.external_drive_ref && (
            <Field label="External drive">{file.external_drive_ref}</Field>
          )}
          <Field label="Uploaded at">{formatDate(file.uploaded_at)}</Field>
          <Field label="Modified at">{formatDate(file.modified_at)}</Field>
          <Field label="Indexed at">{formatDate(file.indexed_at)}</Field>

          <div className="pt-2 border-t border-border">
            <h3 className="text-xs font-semibold uppercase tracking-wide text-muted-foreground mb-2">
              Actions
            </h3>
            <FileActions file={file} />
          </div>
        </div>
      )}
    </Drawer>
  );
}

function Field({
  label,
  children,
  mono,
}: {
  label: string;
  children: React.ReactNode;
  mono?: boolean;
}) {
  return (
    <div>
      <div className="text-xs uppercase tracking-wide text-muted-foreground">{label}</div>
      <div className={mono ? "font-mono text-xs break-all" : ""}>{children}</div>
    </div>
  );
}
