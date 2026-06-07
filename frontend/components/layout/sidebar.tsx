"use client";

import Link from "next/link";
import { usePathname } from "next/navigation";
import { Brain, Search, Upload, Files } from "lucide-react";
import { cn } from "@/lib/utils";

const links = [
  { href: "/", label: "Search", icon: Search },
  { href: "/ingest", label: "Ingest", icon: Upload },
  { href: "/files", label: "Files", icon: Files },
];

export function Sidebar() {
  const pathname = usePathname();
  return (
    <aside className="w-56 border-r border-border bg-card flex flex-col">
      <div className="flex items-center gap-2 p-4 border-b border-border">
        <Brain className="h-5 w-5 text-accent" />
        <span className="font-semibold tracking-tight">DocuMind</span>
      </div>
      <nav className="flex-1 p-2 space-y-1">
        {links.map(({ href, label, icon: Icon }) => {
          const active = pathname === href;
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                active ? "bg-muted text-foreground" : "text-muted-foreground hover:bg-muted hover:text-foreground"
              )}
            >
              <Icon className="h-4 w-4" />
              {label}
            </Link>
          );
        })}
      </nav>
      <div className="border-t border-border p-3 text-xs text-muted-foreground">v0.1.0</div>
    </aside>
  );
}
