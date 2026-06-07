"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Archive, ArchiveRestore, RefreshCw, Trash2, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { ConfirmDialog } from "@/components/ui/confirm";
import type { FileOut } from "@/lib/types";

export function FileActions({ file }: { file: FileOut }) {
  const qc = useQueryClient();
  const [confirmDelete, setConfirmDelete] = useState(false);

  const invalidate = () => qc.invalidateQueries({ queryKey: ["files"] });

  const archive = useMutation({
    mutationFn: () =>
      file.status === "archived" ? api.unarchive(file.id) : api.archive(file.id),
    onSuccess: () => {
      toast.success(file.status === "archived" ? "Unarchived" : "Archived");
      invalidate();
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed"),
  });

  const reindex = useMutation({
    mutationFn: () => api.reindex(file.id),
    onSuccess: () => {
      toast.success("Reindex queued");
      invalidate();
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed"),
  });

  const remove = useMutation({
    mutationFn: () => api.deleteFile(file.id),
    onSuccess: () => {
      toast.success("Deleted");
      invalidate();
    },
    onError: (e) => toast.error(e instanceof Error ? e.message : "Failed"),
  });

  const isArchived = file.status === "archived";

  return (
    <div className="flex items-center gap-1">
      <Button
        variant="ghost"
        size="icon"
        onClick={() => archive.mutate()}
        disabled={archive.isPending}
        title={isArchived ? "Unarchive" : "Archive"}
      >
        {archive.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : isArchived ? (
          <ArchiveRestore className="h-4 w-4" />
        ) : (
          <Archive className="h-4 w-4" />
        )}
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => reindex.mutate()}
        disabled={reindex.isPending}
        title="Reindex"
      >
        {reindex.isPending ? (
          <Loader2 className="h-4 w-4 animate-spin" />
        ) : (
          <RefreshCw className="h-4 w-4" />
        )}
      </Button>
      <Button
        variant="ghost"
        size="icon"
        onClick={() => setConfirmDelete(true)}
        disabled={remove.isPending}
        title="Delete"
        className="text-destructive hover:text-destructive"
      >
        {remove.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Trash2 className="h-4 w-4" />}
      </Button>

      <ConfirmDialog
        open={confirmDelete}
        title="Delete this file?"
        description={`"${file.filename}" will be removed from the index and storage. This cannot be undone.`}
        confirmText="Delete"
        destructive
        onCancel={() => setConfirmDelete(false)}
        onConfirm={async () => {
          await remove.mutateAsync();
          setConfirmDelete(false);
        }}
      />
    </div>
  );
}
