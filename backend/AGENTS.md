# Backend Agent Guide

## Overview

Python FastAPI backend that handles image indexing, semantic search, and image serving.

## Stack

- **FastAPI** — async web framework
- **sentence-transformers** — CLIP model for generating embeddings
- **ChromaDB** — vector database with cosine similarity search
- **Pillow** — image loading and format handling

## Files

| File | Purpose |
|------|---------|
| `main.py` | FastAPI app, routes, request/response models |
| `indexer.py` | `ImageIndexer` class — model loading, indexing, search, ChromaDB ops |
| `requirements.txt` | Python dependencies |
| `Dockerfile` | Container build for deployment |

## How Search Works

1. User sends text query to `/api/search?q=...`
2. CLIP text encoder converts query to a 512-dim vector
3. ChromaDB finds nearest image vectors using cosine distance
4. Results returned with similarity scores (1 - distance)

## How Indexing Works

1. `POST /api/index` with a folder path
2. `ImageIndexer.index_folder()` scans for image files recursively
3. Each image is opened with Pillow, converted to RGB
4. CLIP image encoder produces a 512-dim embedding per image
5. Embeddings + metadata stored in ChromaDB (deduplicated by path hash)

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/search?q=&limit=&offset=` | Semantic search |
| `GET` | `/api/random?limit=` | Random selection |
| `GET` | `/api/recent?limit=&offset=` | Recently indexed |
| `GET` | `/api/images/{id}` | Serve image file |
| `GET` | `/api/download-file/{id}` | Force-download single image |
| `POST` | `/api/download` | ZIP multiple images `{"ids": [...]}` |
| `POST` | `/api/index` | Index folder `{"folder": "...", "limit": N}` |
| `GET` | `/api/stats` | Collection count |

## Running

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

First startup downloads the CLIP model (~350MB) and indexes demo images.

## Important Notes

- The CLIP model downloads on first use — needs internet for initial run
- ChromaDB data persists in `./data/` (or `$DATA_DIR`)
- Image IDs are MD5 hashes of absolute file paths
- Batch size for encoding is 32 images at a time
- `_auto_index_demo_images()` only runs when the collection is empty
