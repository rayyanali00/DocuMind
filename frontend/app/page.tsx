"use client";

import { useMutation } from "@tanstack/react-query";
import { Search as SearchIcon, Loader2, Filter, Sparkles } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { api } from "@/lib/api";
import type { SearchFilters, SearchResponse } from "@/lib/types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { FiltersPanel } from "@/components/search/filters-panel";
import { ResultCard } from "@/components/search/result-card";

export default function SearchPage() {
  const [query, setQuery] = useState("");
  const [filters, setFilters] = useState<SearchFilters>({});
  const [showFilters, setShowFilters] = useState(true);
  const [lastResults, setLastResults] = useState<SearchResponse | null>(null);

  const mutation = useMutation({
    mutationFn: () =>
      api.search({
        query,
        top_k: 10,
        filters,
      }),
    onSuccess: (data) => setLastResults(data),
    onError: (err) => toast.error(err instanceof Error ? err.message : "Search failed"),
  });

  const submit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    mutation.mutate();
  };

  return (
    <div className="flex gap-6">
      {showFilters && (
        <aside className="w-64 shrink-0">
          <div className="rounded-lg border border-border bg-card p-4">
            <h2 className="mb-3 flex items-center gap-2 text-sm font-semibold">
              <Filter className="h-4 w-4" /> Filters
            </h2>
            <FiltersPanel value={filters} onChange={setFilters} />
          </div>
        </aside>
      )}

      <section className="flex-1 min-w-0 space-y-4">
        <form onSubmit={submit} className="flex gap-2">
          <div className="relative flex-1">
            <SearchIcon className="absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="Search across documents, scanned PDFs, YouTube transcripts…"
              className="pl-9 h-11 text-base"
              autoFocus
            />
          </div>
          <Button type="submit" size="lg" disabled={mutation.isPending || !query.trim()}>
            {mutation.isPending ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" /> Searching
              </>
            ) : (
              <>
                <Sparkles className="h-4 w-4" /> Search
              </>
            )}
          </Button>
          <Button
            type="button"
            variant="outline"
            size="lg"
            onClick={() => setShowFilters((v) => !v)}
            aria-label="Toggle filters"
          >
            <Filter className="h-4 w-4" />
          </Button>
        </form>

        {lastResults && (
          <div className="text-xs text-muted-foreground flex items-center gap-3">
            <span>
              {lastResults.total} result{lastResults.total === 1 ? "" : "s"} in{" "}
              {lastResults.elapsed_ms.toFixed(0)} ms
            </span>
            {lastResults.cached && (
              <span className="rounded bg-muted px-1.5 py-0.5">cached</span>
            )}
          </div>
        )}

        {!lastResults && !mutation.isPending && (
          <EmptyState />
        )}

        {lastResults && lastResults.results.length === 0 && (
          <div className="rounded-lg border border-dashed border-border p-10 text-center text-muted-foreground">
            No results. Try a different query or relax your filters.
          </div>
        )}

        <ul className="space-y-3">
          {lastResults?.results.map((r) => (
            <li key={r.file_id}>
              <ResultCard result={r} />
            </li>
          ))}
        </ul>
      </section>
    </div>
  );
}

function EmptyState() {
  return (
    <div className="rounded-lg border border-dashed border-border p-10 text-center">
      <Sparkles className="mx-auto h-8 w-8 text-muted-foreground" />
      <h3 className="mt-3 font-semibold">Search semantically across your library</h3>
      <p className="mt-1 text-sm text-muted-foreground">
        Try a question, a phrase, or a concept — DocuMind blends vector + BM25 retrieval and shows you why each result matched.
      </p>
    </div>
  );
}
