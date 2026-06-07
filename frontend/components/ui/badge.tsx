import { cn } from "@/lib/utils";
import type { HTMLAttributes } from "react";

type Variant = "default" | "outline" | "success" | "warning" | "destructive" | "muted";

const variants: Record<Variant, string> = {
  default: "bg-primary text-primary-foreground",
  outline: "border border-border text-foreground",
  success: "bg-emerald-500/15 text-emerald-700 dark:text-emerald-400",
  warning: "bg-amber-500/15 text-amber-700 dark:text-amber-400",
  destructive: "bg-destructive/15 text-destructive",
  muted: "bg-muted text-muted-foreground",
};

interface Props extends HTMLAttributes<HTMLSpanElement> {
  variant?: Variant;
}

export function Badge({ className, variant = "default", ...props }: Props) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-md px-2 py-0.5 text-xs font-medium",
        variants[variant],
        className
      )}
      {...props}
    />
  );
}
