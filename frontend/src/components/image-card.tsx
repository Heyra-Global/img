"use client";

import { useState } from "react";
import { Download, Plus, Check } from "lucide-react";
import { ImageResult, downloadFile } from "@/lib/api";
import {
  Dialog,
  DialogContent,
  DialogTitle,
  DialogDescription,
} from "@/components/ui/dialog";

type ImageCardProps = {
  image: ImageResult;
  src: string;
  fullSrc: string;
  isSelected: boolean;
  onToggleSelect: () => void;
  priority?: boolean;
};

function getTag(filename: string): string {
  const name = filename.replace(/\.[^.]+$/, "");
  return name;
}

export function ImageCard({
  image,
  src,
  fullSrc,
  isSelected,
  onToggleSelect,
  priority = false,
}: ImageCardProps) {
  const [isOpen, setIsOpen] = useState(false);
  const [loaded, setLoaded] = useState(false);
  const [fullLoaded, setFullLoaded] = useState(false);

  const tag = getTag(image.filename);
  // Reserve exact space before the image loads to prevent grid reflow/jank.
  const aspectRatio =
    image.width && image.height ? `${image.width} / ${image.height}` : undefined;

  function handleDownload(e: React.MouseEvent) {
    e.stopPropagation();
    downloadFile(image.id, image.filename);
  }

  function handleSelect(e: React.MouseEvent) {
    e.stopPropagation();
    onToggleSelect();
  }

  return (
    <>
      <div
        className={`group cursor-pointer relative overflow-hidden break-inside-avoid transition-all duration-150 ${
          isSelected ? "ring-2 ring-primary ring-offset-2 ring-offset-background rounded-sm" : ""
        }`}
        onClick={() => setIsOpen(true)}
      >
        {/* Image (space reserved via aspect-ratio to avoid layout shift) */}
        <div className="relative w-full" style={{ aspectRatio }}>
          {/* eslint-disable-next-line @next/next/no-img-element */}
          <img
            src={src}
            alt={image.filename}
            className={`w-full h-full object-cover transition-opacity duration-300 ${loaded ? "opacity-100" : "opacity-0"}`}
            onLoad={() => setLoaded(true)}
            loading={priority ? "eager" : "lazy"}
            fetchPriority={priority ? "high" : "auto"}
            decoding="async"
          />
          {!loaded && (
            <div className="absolute inset-0 bg-muted animate-pulse" />
          )}
        </div>


        {/* Hover overlay */}
        <div className={`absolute inset-0 pointer-events-none transition-opacity duration-200 ${isSelected ? "opacity-0" : "opacity-0 group-hover:opacity-100"}`}>
          {/* Top title bar */}
          <div className="absolute top-0 left-0 right-0 px-3 py-1.5 pl-10 bg-white/90 text-black text-xs font-mono truncate">
            #{tag}
          </div>
        </div>

        {/* Bottom controls on hover */}
        <div className="absolute bottom-0 left-0 right-0 p-2 opacity-0 group-hover:opacity-100 transition-opacity duration-200 flex items-center justify-between pointer-events-none">
          <div className="flex gap-0.5">
            <div className="h-4 w-4 bg-[#dfb438]" />
            <div className="h-4 w-4 bg-white/80" />
          </div>
          <div className="flex items-center gap-1 pointer-events-auto">
            <button
              onClick={handleSelect}
              className={`p-1.5 rounded transition-colors ${
                isSelected
                  ? "bg-primary text-primary-foreground"
                  : "bg-black/30 hover:bg-black/50 text-white"
              }`}
            >
              {isSelected ? <Check className="h-3.5 w-3.5" /> : <Plus className="h-3.5 w-3.5" />}
            </button>
            <button
              onClick={handleDownload}
              className="p-1.5 rounded bg-black/30 hover:bg-black/50 transition-colors"
            >
              <Download className="h-3.5 w-3.5 text-white" />
            </button>
          </div>
        </div>
      </div>

      <Dialog open={isOpen} onOpenChange={setIsOpen}>
        <DialogContent className="max-w-4xl max-h-[90vh] p-2 bg-card border-border">
          <DialogTitle className="sr-only">{image.filename}</DialogTitle>
          <DialogDescription className="sr-only">
            Full-size preview of {image.filename}
          </DialogDescription>
          {/* Progressive preview: show the cached thumbnail immediately, then
              fade in the full-resolution image once it has loaded. */}
          <div
            className="relative w-full max-h-[85vh] mx-auto"
            style={{ aspectRatio }}
          >
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={src}
              alt=""
              aria-hidden
              className={`absolute inset-0 w-full h-full object-contain transition-opacity duration-300 ${fullLoaded ? "opacity-0" : "opacity-100"}`}
            />
            {/* eslint-disable-next-line @next/next/no-img-element */}
            <img
              src={fullSrc}
              alt={image.filename}
              onLoad={() => setFullLoaded(true)}
              decoding="async"
              className={`relative w-full h-full object-contain transition-opacity duration-300 ${fullLoaded ? "opacity-100" : "opacity-0"}`}
            />
          </div>
          <div className="flex items-center justify-between px-2 py-1">
            <p className="text-sm font-mono text-muted-foreground">#{tag}</p>
            <button
              onClick={handleDownload}
              className="p-1.5 rounded hover:bg-muted transition-colors"
            >
              <Download className="h-4 w-4 text-muted-foreground" />
            </button>
          </div>
        </DialogContent>
      </Dialog>
    </>
  );
}
