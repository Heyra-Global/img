"use client";

import Masonry from "react-masonry-css";
import { ImageResult, getImageUrl } from "@/lib/api";
import { ImageCard } from "./image-card";

type ImageGridProps = {
  images: ImageResult[];
  isLoading: boolean;
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
};

const BREAKPOINTS = {
  default: 3,
  768: 2,
};

export function ImageGrid({ images, isLoading, selected, onToggleSelect }: ImageGridProps) {
  if (isLoading) {
    const heights = [280, 350, 240, 310, 260, 330, 290, 270, 320];
    return (
      <Masonry
        breakpointCols={BREAKPOINTS}
        className="masonry-grid"
        columnClassName="masonry-grid-column"
      >
        {heights.map((h, i) => (
          <div
            key={i}
            className="rounded-lg bg-muted animate-pulse"
            style={{ height: `${h}px` }}
          />
        ))}
      </Masonry>
    );
  }

  if (images.length === 0) {
    return null;
  }

  return (
    <Masonry
      breakpointCols={BREAKPOINTS}
      className="masonry-grid"
      columnClassName="masonry-grid-column"
    >
      {images.map((image) => (
        <ImageCard
          key={image.id}
          image={image}
          src={getImageUrl(image.thumb_url || image.image_url)}
          fullSrc={getImageUrl(image.image_url)}
          isSelected={selected.has(image.id)}
          onToggleSelect={() => onToggleSelect(image.id)}
        />
      ))}
    </Masonry>
  );
}
