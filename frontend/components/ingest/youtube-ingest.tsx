"use client";

import { useMutation } from "@tanstack/react-query";
import { Youtube, Loader2 } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";

export function YoutubeIngest() {
  const [url, setUrl] = useState("");

  const mutation = useMutation({
    mutationFn: () => api.indexYoutube(url.trim()),
    onSuccess: () => {
      toast.success("Queued for transcript ingestion");
      setUrl("");
    },
    onError: (err) =>
      toast.error(err instanceof Error ? err.message : "Failed to submit YouTube URL"),
  });

  return (
    <Card>
      <CardHeader>
        <CardTitle>Index a YouTube video</CardTitle>
        <CardDescription>
          We fetch the public transcript and index it as searchable chunks. Videos without transcripts will fail gracefully.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        <Input
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.youtube.com/watch?v=…"
        />
        <Button disabled={!url.trim() || mutation.isPending} onClick={() => mutation.mutate()}>
          {mutation.isPending ? (
            <>
              <Loader2 className="h-4 w-4 animate-spin" /> Submitting
            </>
          ) : (
            <>
              <Youtube className="h-4 w-4" /> Index transcript
            </>
          )}
        </Button>
      </CardContent>
    </Card>
  );
}
