"use client";

import { Download, X } from "lucide-react";
import { downloadZip } from "@/lib/api";
import { useState } from "react";

type SelectionBarProps = {
  selected: Set<string>;
  onClear: () => void;
};

export function SelectionBar({ selected, onClear }: SelectionBarProps) {
  const [isDownloading, setIsDownloading] = useState(false);
  const count = selected.size;

  if (count === 0) return null;

  async function handleDownload() {
    setIsDownloading(true);
    try {
      await downloadZip(Array.from(selected));
    } catch {
      // TODO: toast error
    } finally {
      setIsDownloading(false);
    }
  }

  return (
    <div className="fixed bottom-6 left-1/2 -translate-x-1/2 z-50">
      <div className="flex items-center gap-4 px-5 py-3 rounded-2xl bg-white/5 backdrop-blur-sm shadow-[0_4px_30px_rgba(0,0,0,0.4)]">
        <span className="text-sm text-foreground">
          {count} image{count > 1 ? "s" : ""} selected
        </span>

        <button
          onClick={handleDownload}
          disabled={isDownloading}
          className="flex items-center gap-2 px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium hover:bg-primary/90 transition-colors disabled:opacity-50"
        >
          {isDownloading ? (
            <div className="h-4 w-4 border-2 border-primary-foreground border-t-transparent rounded-full animate-spin" />
          ) : (
            <Download className="h-4 w-4" />
          )}
          Download ZIP
        </button>

        <button
          onClick={onClear}
          className="p-1.5 rounded-lg text-muted-foreground hover:text-foreground hover:bg-white/10 transition-colors"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
    </div>
  );
}
