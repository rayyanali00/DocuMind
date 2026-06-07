"use client";

import { useMutation } from "@tanstack/react-query";
import { FolderSearch, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function DirectoryIngest() {
  const [path, setPath] = useState("");
  const [drive, setDrive] = useState("");

  const mutation = useMutation({
    mutationFn: () => api.ingestDirectory(path.trim(), drive.trim() || undefined),
    onSuccess: (data) =>
      toast.success(
        `Discovered ${data.discovered}, queued ${data.accepted} (${data.skipped} skipped)`
      ),
    onError: (err) => toast.error(err instanceof Error ? err.message : "Failed to ingest directory"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Ingest a directory</CardTitle>
        <CardDescription>
          The backend recursively scans this path on the server. Provide an absolute path the API container can read (e.g. a mounted volume or external drive).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <div>
          <label className="text-xs font-medium text-muted-foreground">Absolute path</label>
          <Input
            value={path}
            onChange={(e) => setPath(e.target.value)}
            placeholder="/data/external-drive/research"
            className="mt-1"
          />
        </div>
        <div>
          <label className="text-xs font-medium text-muted-foreground">
            External drive label (optional)
          </label>
          <Input
            value={drive}
            onChange={(e) => setDrive(e.target.value)}
            placeholder="e.g. blue-ssd-2tb"
            className="mt-1"
          />
        </div>
        <Button
          disabled={!path.trim() || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          {mutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Scanning…
            </>
          ) : (
            <>
              <FolderSearch className="h-4 w-4" /> Scan & ingest
            </>
          )}
        </Button>

        {mutation.data && (
          <div className="mt-3 rounded-md bg-muted/50 p-3 text-sm">
            <div className="font-mono text-xs text-muted-foreground">{mutation.data.directory}</div>
            <div className="mt-1">
              Discovered <b>{mutation.data.discovered}</b>, accepted{" "}
              <b>{mutation.data.accepted}</b>, skipped <b>{mutation.data.skipped}</b>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
