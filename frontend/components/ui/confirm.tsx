"use client";

import { Button } from "./button";
import { useState } from "react";

interface Props {
  open: boolean;
  title: string;
  description?: string;
  confirmText?: string;
  destructive?: boolean;
  onConfirm: () => Promise<void> | void;
  onCancel: () => void;
}

export function ConfirmDialog({
  open,
  title,
  description,
  confirmText = "Confirm",
  destructive,
  onConfirm,
  onCancel,
}: Props) {
  const [loading, setLoading] = useState(false);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/50 p-4">
      <div className="w-full max-w-md rounded-lg border border-border bg-card p-6 shadow-xl">
        <h3 className="font-semibold text-lg">{title}</h3>
        {description && (
          <p className="mt-2 text-sm text-muted-foreground">{description}</p>
        )}
        <div className="mt-6 flex justify-end gap-2">
          <Button variant="outline" onClick={onCancel} disabled={loading}>
            Cancel
          </Button>
          <Button
            variant={destructive ? "destructive" : "default"}
            disabled={loading}
            onClick={async () => {
              setLoading(true);
              try {
                await onConfirm();
              } finally {
                setLoading(false);
              }
            }}
          >
            {loading ? "Working…" : confirmText}
          </Button>
        </div>
      </div>
    </div>
  );
}
