const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export type Orientation = "horizontal" | "vertical";

export type ImageResult = {
  id: string;
  filename: string;
  path: string;
  image_url: string;
  thumb_url?: string;
  score?: number;
  orientation?: string;
  width?: number;
  height?: number;
};

type SearchResponse = {
  query: string;
  results: ImageResult[];
  total: number;
};

type RecentResponse = {
  results: ImageResult[];
  total: number;
};

type StatsResponse = {
  total_images: number;
  images_dir: string;
};

type IndexResponse = {
  indexed: number;
  skipped: number;
  total: number;
  duration_seconds: number;
};

export function getImageUrl(imageUrl: string): string {
  if (imageUrl.startsWith("http")) return imageUrl;
  return `${API_BASE}${imageUrl}`;
}

function orientationParam(orientation?: Orientation): string {
  return orientation ? `&orientation=${orientation}` : "";
}

export async function searchImages(
  query: string,
  limit = 20,
  offset = 0,
  orientation?: Orientation
): Promise<SearchResponse> {
  const res = await fetch(
    `${API_BASE}/api/search?q=${encodeURIComponent(query)}&limit=${limit}&offset=${offset}${orientationParam(orientation)}`
  );
  if (!res.ok) throw new Error("Search failed");
  return res.json();
}

export async function getRecentImages(
  limit = 20,
  offset = 0,
  orientation?: Orientation
): Promise<RecentResponse> {
  const res = await fetch(
    `${API_BASE}/api/recent?limit=${limit}&offset=${offset}${orientationParam(orientation)}`
  );
  if (!res.ok) throw new Error("Failed to fetch recent images");
  return res.json();
}

export async function getRandomImages(
  limit = 20,
  orientation?: Orientation
): Promise<RecentResponse> {
  const res = await fetch(
    `${API_BASE}/api/random?limit=${limit}${orientationParam(orientation)}`
  );
  if (!res.ok) throw new Error("Failed to fetch random images");
  return res.json();
}

export async function downloadFile(imageId: string, filename: string): Promise<void> {
  const res = await fetch(`${API_BASE}/api/download-file/${imageId}`);
  if (!res.ok) throw new Error("Download failed");
  const blob = await res.blob();
  const blobUrl = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = blobUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(blobUrl);
}

export async function getStats(): Promise<StatsResponse> {
  const res = await fetch(`${API_BASE}/api/stats`);
  if (!res.ok) throw new Error("Failed to fetch stats");
  return res.json();
}

export async function indexImages(folder?: string): Promise<IndexResponse> {
  const res = await fetch(`${API_BASE}/api/index`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ folder: folder || null }),
  });
  if (!res.ok) throw new Error("Indexing failed");
  return res.json();
}

export async function downloadZip(ids: string[]): Promise<void> {
  const res = await fetch(`${API_BASE}/api/download`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ ids }),
  });
  if (!res.ok) throw new Error("Download failed");

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = "images.zip";
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  URL.revokeObjectURL(url);
}
