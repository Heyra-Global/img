import io
import os
import threading
import time
import zipfile
from pathlib import Path
from contextlib import asynccontextmanager
from typing import Optional

from fastapi import FastAPI, Query, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

from indexer import ImageIndexer

IMAGES_DIR = os.environ.get("IMAGES_DIR", "./images")
DATA_DIR = os.environ.get("DATA_DIR", "./data")

indexer: Optional[ImageIndexer] = None

WARMUP_QUERIES = [
    "nature", "ocean", "city", "business", "people", "technology",
    "abstract", "food", "travel", "green", "blue", "dark", "minimal",
    "office", "building", "landscape", "portrait", "product", "art",
    "background", "light", "colorful", "sky", "water", "person",
]


def _startup_tasks():
    # Tag any images missing orientation, then pre-warm common search
    # embeddings so the first real search for popular terms is instant.
    indexer.backfill_orientation()
    indexer.warm_queries(WARMUP_QUERIES)


@asynccontextmanager
async def lifespan(app: FastAPI):
    global indexer
    indexer = ImageIndexer(persist_dir=DATA_DIR)
    # Run on a background thread so startup isn't blocked by the warmup.
    threading.Thread(target=_startup_tasks, daemon=True).start()
    yield


app = FastAPI(title="img – Semantic Image Search", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class IndexRequest(BaseModel):
    folder: Optional[str] = None
    limit: Optional[int] = None


class IndexResponse(BaseModel):
    indexed: int
    skipped: int
    total: int
    duration_seconds: float


class SearchResult(BaseModel):
    id: str
    filename: str
    path: str
    image_url: str
    thumb_url: str
    score: float
    orientation: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total: int


class StatsResponse(BaseModel):
    total_images: int
    images_dir: str


@app.post("/api/index", response_model=IndexResponse)
async def index_images(request: IndexRequest):
    folder = request.folder or IMAGES_DIR
    folder_path = Path(folder).resolve()

    if not folder_path.exists():
        raise HTTPException(status_code=400, detail=f"Folder not found: {folder}")

    start = time.time()
    indexed, skipped = indexer.index_folder(str(folder_path), limit=request.limit)
    duration = time.time() - start

    return IndexResponse(
        indexed=indexed,
        skipped=skipped,
        total=indexer.total_images(),
        duration_seconds=round(duration, 2),
    )


def _image_url(image_id: str, filename: str) -> str:
    return f"/api/images/{image_id}"


def _thumb_url(image_id: str, filename: str) -> str:
    return f"/api/images/{image_id}"


def _serialize(r: dict) -> dict:
    return {
        "id": r["id"],
        "filename": r["filename"],
        "path": r["path"],
        "image_url": _image_url(r["id"], r["filename"]),
        "thumb_url": _thumb_url(r["id"], r["filename"]),
        "orientation": r.get("orientation"),
        "width": r.get("width"),
        "height": r.get("height"),
    }


@app.get("/api/search", response_model=SearchResponse)
async def search_images(
    q: str = Query(..., min_length=1, description="Search query"),
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    orientation: Optional[str] = Query(
        None, pattern="^(horizontal|vertical|square)$"
    ),
):
    results = indexer.search(q, n_results=limit + offset, orientation=orientation)

    search_results = []
    for r in results[offset:]:
        search_results.append(
            SearchResult(
                id=r["id"],
                filename=r["filename"],
                path=r["path"],
                image_url=_image_url(r["id"], r["filename"]),
                thumb_url=_thumb_url(r["id"], r["filename"]),
                score=r["score"],
                orientation=r.get("orientation"),
                width=r.get("width"),
                height=r.get("height"),
            )
        )

    return SearchResponse(query=q, results=search_results, total=len(search_results))


@app.get("/api/recent")
async def recent_images(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    orientation: Optional[str] = Query(
        None, pattern="^(horizontal|vertical|square)$"
    ),
):
    results = indexer.get_recent(limit + offset, orientation=orientation)
    paginated = results[offset:]
    return {
        "results": [_serialize(r) for r in paginated],
        "total": len(paginated),
    }


@app.get("/api/random")
async def random_images(
    limit: int = Query(20, ge=1, le=100),
    orientation: Optional[str] = Query(
        None, pattern="^(horizontal|vertical|square)$"
    ),
):
    results = indexer.get_random(limit, orientation=orientation)
    return {
        "results": [_serialize(r) for r in results],
        "total": len(results),
    }


@app.get("/api/images/{image_id}")
async def serve_image(image_id: str):
    path = indexer.get_image_path(image_id)
    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(path)


@app.get("/api/download-file/{image_id}")
async def download_file(image_id: str):
    """Download a single image with Content-Disposition to force save-to-disk."""
    results = indexer.collection.get(ids=[image_id], include=["metadatas"])
    if not results["ids"]:
        raise HTTPException(status_code=404, detail="Image not found")

    metadata = results["metadatas"][0]
    filename = metadata["filename"]
    path = metadata.get("path", "")

    if not path or not Path(path).exists():
        raise HTTPException(status_code=404, detail="Image not found")
    return FileResponse(
        path,
        filename=filename,
        media_type="application/octet-stream",
    )


@app.get("/api/stats", response_model=StatsResponse)
async def stats():
    return StatsResponse(
        total_images=indexer.total_images(),
        images_dir=str(Path(IMAGES_DIR).resolve()),
    )


class DownloadRequest(BaseModel):
    ids: list[str]


@app.post("/api/download")
async def download_zip(request: DownloadRequest):
    if not request.ids:
        raise HTTPException(status_code=400, detail="No images selected")

    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as zf:
        for image_id in request.ids:
            path = indexer.get_image_path(image_id)
            if path and Path(path).exists():
                zf.write(path, Path(path).name)

    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/zip",
        headers={"Content-Disposition": "attachment; filename=images.zip"},
    )
