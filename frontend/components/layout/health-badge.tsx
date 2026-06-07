"use client";

import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";

export function HealthBadge() {
  const { data, isError, isLoading } = useQuery({
    queryKey: ["health"],
    queryFn: () => api.health(),
    refetchInterval: 15_000,
    staleTime: 10_000,
  });

  if (isLoading) return <Badge variant="muted">checking…</Badge>;
  if (isError || !data) return <Badge variant="destructive">offline</Badge>;

  const variant = data.status === "ok" ? "success" : "warning";
  const allUp = Object.values(data.dependencies).every(Boolean);

  return (
    <div className="flex items-center gap-2">
      <Badge variant={variant}>
        <span
          className={cn(
            "mr-1.5 h-2 w-2 rounded-full",
            allUp ? "bg-emerald-500" : "bg-amber-500"
          )}
        />
        {allUp ? "All systems go" : "Degraded"}
      </Badge>
    </div>
  );
}
