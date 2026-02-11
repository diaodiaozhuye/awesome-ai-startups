"use client";

import { useEffect, useRef, useState } from "react";

interface SearchBarProps {
  placeholder: string;
  onSearch: (query: string) => void;
  debounceMs?: number;
}

export function SearchBar({ placeholder, onSearch, debounceMs = 300 }: SearchBarProps) {
  const [value, setValue] = useState("");
  const timerRef = useRef<ReturnType<typeof setTimeout>>(undefined);

  useEffect(() => {
    timerRef.current = setTimeout(() => {
      onSearch(value);
    }, debounceMs);

    return () => clearTimeout(timerRef.current);
  }, [value, debounceMs, onSearch]);

  return (
    <input
      type="text"
      value={value}
      onChange={(e) => setValue(e.target.value)}
      placeholder={placeholder}
      className="w-full rounded-lg border border-border bg-background px-4 py-3 text-sm placeholder:text-muted-foreground focus:outline-none focus:ring-2 focus:ring-primary/50"
    />
  );
}
