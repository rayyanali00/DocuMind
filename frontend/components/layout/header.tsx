"use client";

import { usePathname } from "next/navigation";
import { ThemeToggle } from "./theme-toggle";
import { HealthBadge } from "./health-badge";

const titles: Record<string, string> = {
  "/": "Search",
  "/ingest": "Ingest",
  "/files": "Files",
};

export function Header() {
  const pathname = usePathname();
  return (
    <header className="h-14 border-b border-border bg-card/50 backdrop-blur flex items-center justify-between px-6">
      <h1 className="font-semibold">{titles[pathname] || "DocuMind"}</h1>
      <div className="flex items-center gap-3">
        <HealthBadge />
        <ThemeToggle />
      </div>
    </header>
  );
}
