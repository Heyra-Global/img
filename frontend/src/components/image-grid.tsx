"use client";

import { useEffect, useState } from "react";
import { ImageResult, getImageUrl } from "@/lib/api";
import { ImageCard } from "./image-card";

type ImageGridProps = {
  images: ImageResult[];
  isLoading: boolean;
  selected: Set<string>;
  onToggleSelect: (id: string) => void;
};

const MOBILE_BREAKPOINT = "(max-width: 768px)";

// Sync column count with the viewport (external system): 2 columns on mobile,
// 3 otherwise.
function useColumnCount(): number {
  const [columns, setColumns] = useState(3);
  useEffect(() => {
    const mq = window.matchMedia(MOBILE_BREAKPOINT);
    const update = () => setColumns(mq.matches ? 2 : 3);
    update();
    mq.addEventListener("change", update);
    return () => mq.removeEventListener("change", update);
  }, []);
  return columns;
}

type Placed = { image: ImageResult; index: number };

// Greedily place each image into the currently shortest column using its real
// aspect ratio, so columns stay balanced instead of one running far ahead.
function balanceColumns(images: ImageResult[], columnCount: number): Placed[][] {
  const columns: Placed[][] = Array.from({ length: columnCount }, () => []);
  const heights = new Array(columnCount).fill(0);

  images.forEach((image, index) => {
    const ratio =
      image.width && image.height ? image.height / image.width : 1;
    let shortest = 0;
    for (let c = 1; c < columnCount; c++) {
      if (heights[c] < heights[shortest]) shortest = c;
    }
    columns[shortest].push({ image, index });
    heights[shortest] += ratio;
  });

  return columns;
}

export function ImageGrid({ images, isLoading, selected, onToggleSelect }: ImageGridProps) {
  const columnCount = useColumnCount();

  if (isLoading) {
    const heights = [280, 350, 240, 310, 260, 330, 290, 270, 320];
    const skeletonColumns: number[][] = Array.from({ length: columnCount }, () => []);
    heights.forEach((h, i) => skeletonColumns[i % columnCount].push(h));
    return (
      <div className="masonry-grid">
        {skeletonColumns.map((col, ci) => (
          <div className="masonry-grid-column" key={ci}>
            {col.map((h, i) => (
              <div
                key={i}
                className="rounded-lg bg-muted animate-pulse"
                style={{ height: `${h}px` }}
              />
            ))}
          </div>
        ))}
      </div>
    );
  }

  if (images.length === 0) {
    return null;
  }

  const columns = balanceColumns(images, columnCount);

  return (
    <div className="masonry-grid">
      {columns.map((col, ci) => (
        <div className="masonry-grid-column" key={ci}>
          {col.map(({ image, index }) => (
            <ImageCard
              key={image.id}
              image={image}
              src={getImageUrl(image.thumb_url || image.image_url)}
              fullSrc={getImageUrl(image.image_url)}
              isSelected={selected.has(image.id)}
              onToggleSelect={() => onToggleSelect(image.id)}
              priority={index < 6}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
