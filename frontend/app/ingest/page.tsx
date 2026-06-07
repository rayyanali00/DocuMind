"use client";

import { useState } from "react";
import { Upload, FolderSearch, Youtube } from "lucide-react";
import { cn } from "@/lib/utils";

import { FileUpload } from "@/components/ingest/file-upload";
import { DirectoryIngest } from "@/components/ingest/directory-ingest";
import { YoutubeIngest } from "@/components/ingest/youtube-ingest";

type Tab = "upload" | "directory" | "youtube";

const tabs: { id: Tab; label: string; icon: typeof Upload }[] = [
  { id: "upload", label: "Upload files", icon: Upload },
  { id: "directory", label: "Scan directory", icon: FolderSearch },
  { id: "youtube", label: "YouTube transcript", icon: Youtube },
];

export default function IngestPage() {
  const [tab, setTab] = useState<Tab>("upload");

  return (
    <div className="space-y-6 max-w-3xl">
      <div className="flex gap-1 rounded-lg border border-border bg-card p-1 w-fit">
        {tabs.map(({ id, label, icon: Icon }) => (
          <button
            key={id}
            onClick={() => setTab(id)}
            className={cn(
              "flex items-center gap-2 rounded-md px-3 py-1.5 text-sm font-medium transition-colors",
              tab === id
                ? "bg-muted text-foreground"
                : "text-muted-foreground hover:bg-muted/50"
            )}
          >
            <Icon className="h-4 w-4" />
            {label}
          </button>
        ))}
      </div>

      {tab === "upload" && <FileUpload />}
      {tab === "directory" && <DirectoryIngest />}
      {tab === "youtube" && <YoutubeIngest />}
    </div>
  );
}
