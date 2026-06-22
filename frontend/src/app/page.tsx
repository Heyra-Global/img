"use client";

import { useCallback, useEffect, useRef, useState, useTransition } from "react";
import { SearchBar } from "@/components/search-bar";
import { ImageGrid } from "@/components/image-grid";
import { SelectionBar } from "@/components/selection-bar";
import { OrientationFilter } from "@/components/orientation-filter";
import {
  ImageResult,
  Orientation,
  searchImages,
  getRecentImages,
  getRandomImages,
  getStats,
} from "@/lib/api";

const PAGE_SIZE = 20;

function scrollToTop() {
  if (typeof window !== "undefined") {
    window.scrollTo({ top: 0, behavior: "auto" });
  }
}

export default function Home() {
  const [query, setQuery] = useState("");
  const [orientation, setOrientation] = useState<Orientation | null>(null);
  const [images, setImages] = useState<ImageResult[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [isLoading, setIsLoading] = useState(true);
  const [isLoadingMore, setIsLoadingMore] = useState(false);
  const [hasMore, setHasMore] = useState(true);
  const [hasSearched, setHasSearched] = useState(false);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [, startTransition] = useTransition();
  const observerRef = useRef<IntersectionObserver>(undefined);
  const loadMoreRef = useRef<() => Promise<void>>(undefined);

  useEffect(() => {
    getStats().catch(() => {});
  }, []);

  useEffect(() => {
    if (!query) {
      setHasSearched(false);
      setIsLoading(true);
      setHasMore(true);
      scrollToTop();
      getRandomImages(PAGE_SIZE, orientation ?? undefined)
        .catch(() => getRecentImages(PAGE_SIZE, 0, orientation ?? undefined))
        .then((res) => {
          startTransition(() => {
            setImages(res.results);
            setHasMore(res.results.length >= PAGE_SIZE);
          });
        })
        .catch(() => setImages([]))
        .finally(() => setIsLoading(false));
    }
  }, [query, orientation]);

  const handleSearch = useCallback(
    async (q: string) => {
      if (!q.trim()) return;
      setIsSearching(true);
      setHasSearched(true);
      setHasMore(true);
      scrollToTop();
      try {
        const res = await searchImages(q.trim(), PAGE_SIZE, 0, orientation ?? undefined);
        startTransition(() => {
          setImages(res.results);
          setHasMore(res.results.length >= PAGE_SIZE);
        });
      } catch {
        setImages([]);
      } finally {
        setIsSearching(false);
      }
    },
    [orientation]
  );

  useEffect(() => {
    if (!query.trim()) return;
    const timer = setTimeout(() => handleSearch(query), 150);
    return () => clearTimeout(timer);
  }, [query, handleSearch]);

  const loadMore = useCallback(async () => {
    if (isLoadingMore || !hasMore) return;
    setIsLoadingMore(true);
    try {
      const offset = images.length;
      const res = query.trim()
        ? await searchImages(query.trim(), PAGE_SIZE, offset, orientation ?? undefined)
        : await getRecentImages(PAGE_SIZE, offset, orientation ?? undefined);
      const newImages = res.results;
      startTransition(() => {
        setImages((prev) => [...prev, ...newImages]);
        setHasMore(newImages.length >= PAGE_SIZE);
      });
    } catch {
      setHasMore(false);
    } finally {
      setIsLoadingMore(false);
    }
  }, [images.length, query, orientation, isLoadingMore, hasMore]);

  loadMoreRef.current = loadMore;

  const loaderCallbackRef = useCallback((node: HTMLDivElement | null) => {
    if (observerRef.current) {
      observerRef.current.disconnect();
    }
    if (node) {
      observerRef.current = new IntersectionObserver(
        (entries) => {
          if (entries[0].isIntersecting) {
            loadMoreRef.current?.();
          }
        },
        { rootMargin: "400px" }
      );
      observerRef.current.observe(node);
    }
  }, []);

  function toggleSelect(id: string) {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return next;
    });
  }

  function clearSelection() {
    setSelected(new Set());
  }

  return (
    <main className="flex-1 flex flex-col">
      {/* Floating header */}
      <header className="sticky top-0 z-50 w-full px-4 sm:px-6 lg:px-8 pt-4">
        <div className="max-w-7xl mx-auto flex items-center gap-4 px-6 py-3 rounded-2xl bg-white/5 backdrop-blur-sm shadow-[0_2px_20px_rgba(0,0,0,0.3)]">
          <h1 className="text-sm font-medium text-foreground whitespace-nowrap">
            img
          </h1>
          <SearchBar
            value={query}
            onChange={setQuery}
            isSearching={isSearching}
          />
          <OrientationFilter value={orientation} onChange={setOrientation} />
        </div>
      </header>

      {/* Results area */}
      <div className="flex-1 w-full max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 pb-24">
        {hasSearched && images.length === 0 && !isSearching && (
          <p className="text-center text-muted-foreground py-12">
            No images found for &ldquo;{query}&rdquo;. Try a different search term.
          </p>
        )}

        <ImageGrid
          images={images}
          isLoading={isLoading && !hasSearched}
          selected={selected}
          onToggleSelect={toggleSelect}
        />

        {/* Infinite scroll trigger */}
        {hasMore && images.length > 0 && (
          <div ref={loaderCallbackRef} className="py-8 flex justify-center">
            {isLoadingMore && (
              <div className="h-6 w-6 border-2 border-muted-foreground/30 border-t-muted-foreground rounded-full animate-spin" />
            )}
          </div>
        )}
      </div>

      {/* Selection bar */}
      <SelectionBar selected={selected} onClear={clearSelection} />
    </main>
  );
}
