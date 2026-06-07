"use client";

import { Moon, Sun, Monitor } from "lucide-react";
import { useTheme } from "next-themes";
import { useEffect, useState } from "react";
import { Button } from "@/components/ui/button";

export function ThemeToggle() {
  const { theme, setTheme } = useTheme();
  const [mounted, setMounted] = useState(false);
  useEffect(() => setMounted(true), []);

  if (!mounted) {
    return <Button variant="ghost" size="icon" aria-label="Toggle theme" />;
  }

  const next = theme === "light" ? "dark" : theme === "dark" ? "system" : "light";
  const Icon = theme === "dark" ? Moon : theme === "system" ? Monitor : Sun;

  return (
    <Button
      variant="ghost"
      size="icon"
      aria-label="Toggle theme"
      title={`Theme: ${theme} (click for ${next})`}
      onClick={() => setTheme(next)}
    >
      <Icon className="h-4 w-4" />
    </Button>
  );
}
