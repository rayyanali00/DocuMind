"use client";

import { useMutation } from "@tanstack/react-query";
import { Upload, Loader2, FileCheck2, FileX2 } from "lucide-react";
import { useRef, useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { formatBytes, cn } from "@/lib/utils";

interface UploadJob {
  id: string;
  file: File;
  status: "pending" | "uploading" | "done" | "error";
  message?: string;
}

export function FileUpload() {
  const [jobs, setJobs] = useState<UploadJob[]>([]);
  const [dragOver, setDragOver] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const uploadOne = useMutation({
    mutationFn: ({ file }: { file: File }) => api.uploadFile(file),
  });

  const startUploads = async (files: FileList | File[]) => {
    const newJobs: UploadJob[] = Array.from(files).map((file) => ({
      id: crypto.randomUUID(),
      file,
      status: "pending",
    }));
    setJobs((prev) => [...newJobs, ...prev]);

    for (const job of newJobs) {
      setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, status: "uploading" } : j)));
      try {
        await uploadOne.mutateAsync({ file: job.file });
        setJobs((prev) => prev.map((j) => (j.id === job.id ? { ...j, status: "done" } : j)));
      } catch (err) {
        const msg = err instanceof Error ? err.message : "Upload failed";
        toast.error(`${job.file.name}: ${msg}`);
        setJobs((prev) =>
          prev.map((j) => (j.id === job.id ? { ...j, status: "error", message: msg } : j))
        );
      }
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>Upload files</CardTitle>
        <CardDescription>
          PDF, DOCX, TXT, CSV, XLSX, PPTX, PNG, JPG, JPEG, TIFF. Scanned PDFs and images go through OCR automatically.
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div
          onDragOver={(e) => {
            e.preventDefault();
            setDragOver(true);
          }}
          onDragLeave={() => setDragOver(false)}
          onDrop={(e) => {
            e.preventDefault();
            setDragOver(false);
            if (e.dataTransfer.files.length) void startUploads(e.dataTransfer.files);
          }}
          className={cn(
            "rounded-lg border-2 border-dashed p-8 text-center transition-colors",
            dragOver ? "border-accent bg-accent/5" : "border-border"
          )}
        >
          <Upload className="mx-auto h-8 w-8 text-muted-foreground" />
          <p className="mt-2 text-sm">Drag & drop files here</p>
          <p className="text-xs text-muted-foreground">or</p>
          <Button
            variant="outline"
            className="mt-2"
            onClick={() => inputRef.current?.click()}
          >
            Choose files
          </Button>
          <input
            ref={inputRef}
            type="file"
            multiple
            className="hidden"
            onChange={(e) => {
              if (e.target.files) void startUploads(e.target.files);
              e.target.value = "";
            }}
          />
        </div>

        {jobs.length > 0 && (
          <ul className="mt-4 space-y-2 max-h-72 overflow-y-auto">
            {jobs.map((j) => (
              <li
                key={j.id}
                className="flex items-center justify-between rounded-md border border-border p-2 text-sm"
              >
                <div className="min-w-0 flex items-center gap-2">
                  {j.status === "uploading" && (
                    <Loader2 className="h-4 w-4 animate-spin text-muted-foreground" />
                  )}
                  {j.status === "done" && (
                    <FileCheck2 className="h-4 w-4 text-emerald-500" />
                  )}
                  {j.status === "error" && (
                    <FileX2 className="h-4 w-4 text-destructive" />
                  )}
                  <span className="truncate">{j.file.name}</span>
                </div>
                <span className="text-xs text-muted-foreground">
                  {j.status === "error" ? j.message : formatBytes(j.file.size)}
                </span>
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
