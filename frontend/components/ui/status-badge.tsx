import { Badge } from "./badge";
import type { FileStatus } from "@/lib/types";

const map: Record<FileStatus, { label: string; variant: "success" | "warning" | "destructive" | "muted" | "default" }> = {
  pending: { label: "Pending", variant: "muted" },
  processing: { label: "Processing", variant: "warning" },
  indexed: { label: "Indexed", variant: "success" },
  failed: { label: "Failed", variant: "destructive" },
  archived: { label: "Archived", variant: "muted" },
};

export function StatusBadge({ status }: { status: FileStatus }) {
  const cfg = map[status];
  return <Badge variant={cfg.variant}>{cfg.label}</Badge>;
}
