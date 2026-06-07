"use client";

import { useEffect } from "react";
import { X } from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "./button";

interface Props {
  open: boolean;
  onClose: () => void;
  title?: string;
  children: React.ReactNode;
  width?: string;
}

export function Drawer({ open, onClose, title, children, width = "max-w-xl" }: Props) {
  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => e.key === "Escape" && onClose();
    document.addEventListener("keydown", onKey);
    return () => document.removeEventListener("keydown", onKey);
  }, [open, onClose]);

  return (
    <>
      <div
        onClick={onClose}
        className={cn(
          "fixed inset-0 z-40 bg-black/40 transition-opacity",
          open ? "opacity-100" : "pointer-events-none opacity-0"
        )}
      />
      <aside
        className={cn(
          "fixed inset-y-0 right-0 z-50 w-full bg-card text-card-foreground border-l border-border shadow-xl",
          "transition-transform duration-200",
          width,
          open ? "translate-x-0" : "translate-x-full"
        )}
      >
        <div className="flex items-center justify-between border-b border-border p-4">
          <h2 className="font-semibold">{title}</h2>
          <Button variant="ghost" size="icon" onClick={onClose} aria-label="Close">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <div className="overflow-y-auto p-4 h-[calc(100%-3.5rem)]">{children}</div>
      </aside>
    </>
  );
}
