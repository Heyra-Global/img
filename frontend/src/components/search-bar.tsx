"use client";

import { Search, X } from "lucide-react";
import { Input } from "@/components/ui/input";
import { useRef } from "react";

type SearchBarProps = {
  value: string;
  onChange: (value: string) => void;
  isSearching: boolean;
};

export function SearchBar({ value, onChange, isSearching }: SearchBarProps) {
  const inputRef = useRef<HTMLInputElement>(null);

  return (
    <div className="relative w-full">
      <Search className="absolute left-4 top-1/2 -translate-y-1/2 h-5 w-5 text-muted-foreground" />
      <Input
        ref={inputRef}
        type="text"
        placeholder="Search images... try 'green', 'banking', 'outdoor'"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="pl-12 pr-12 h-12 text-base rounded-2xl bg-secondary border-none shadow-none text-foreground placeholder:text-muted-foreground focus-visible:ring-0 focus-visible:outline-none focus-visible:bg-secondary/80"
      />
      {value && !isSearching && (
        <button
          onClick={() => {
            onChange("");
            inputRef.current?.focus();
          }}
          className="absolute right-4 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground transition-colors"
        >
          <X className="h-5 w-5" />
        </button>
      )}
      {isSearching && (
        <div className="absolute right-4 top-1/2 -translate-y-1/2">
          <div className="h-4 w-4 border-2 border-primary border-t-transparent rounded-full animate-spin" />
        </div>
      )}
    </div>
  );
}
