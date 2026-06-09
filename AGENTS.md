# Agent Guide

> Context file for AI coding assistants working on this project.

## What is this?

**img** is a self-hosted semantic image search tool. Users type natural language queries (e.g. "sunset", "person in red") and the system returns visually matching images using CLIP embeddings.

## Architecture

```
┌─────────────┐       HTTP        ┌─────────────────┐
│   Frontend  │ ◄──────────────── │     Backend     │
│  (Next.js)  │   localhost:3000  │    (FastAPI)    │
│             │ ──────────────►   │  localhost:8000 │
└─────────────┘                   └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │    ChromaDB     │
                                  │ (vector store)  │
                                  └────────┬────────┘
                                           │
                                  ┌────────▼────────┐
                                  │  CLIP ViT-B/32  │
                                  │ (embeddings)    │
                                  └─────────────────┘
```

## Quick Setup (development)

```bash
# Terminal 1 – backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload

# Terminal 2 – frontend
cd frontend
npm install
npm run dev
```

Demo images auto-index on first startup. Open http://localhost:3000.

## Key Design Decisions

- **CLIP ViT-B/32** via `sentence-transformers` — encodes both images and text into the same vector space for semantic similarity
- **ChromaDB** — local file-based vector database, no external services needed
- **No cloud dependencies** — everything runs locally by default
- **Auto-indexing** — if the DB is empty on startup, demo images are indexed automatically

## Project Structure

```
img/
├── backend/
│   ├── main.py           # FastAPI app, all API endpoints
│   ├── indexer.py        # CLIP model loading, ChromaDB operations
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── app/          # Next.js App Router pages
│   │   ├── components/   # React components
│   │   └── lib/          # API client, utilities
│   ├── package.json
│   └── tsconfig.json
├── demo-images/          # 8 sample images for testing
├── .env.example
├── README.md
└── LICENSE
```

## Common Tasks

### Add a new API endpoint

1. Define the route in `backend/main.py`
2. If it needs indexer access, use the global `indexer` instance
3. Add the corresponding client function in `frontend/src/lib/api.ts`

### Add a new frontend component

1. Create in `frontend/src/components/`
2. Use shadcn/ui primitives from `frontend/src/components/ui/`
3. Import in the page or parent component

### Index new images

```bash
curl -X POST http://localhost:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"folder": "/absolute/path/to/images"}'
```

### Reset the database

Delete `backend/data/` and restart the backend. Demo images re-index automatically.

## Environment Variables

| Variable | Default | Used by |
|----------|---------|---------|
| `IMAGES_DIR` | `./images` | Backend |
| `DATA_DIR` | `./data` | Backend |
| `DEMO_IMAGES_DIR` | `./demo-images` | Backend |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Frontend |

## Testing Search Quality

The demo images are chosen to validate semantic search:
- "green" → should return `HEYRA423.png` and the green grapes image
- "red" → should return `HEYRA168.png` and the red grape clusters
- "wine" or "glass" → should return the minimalist wine study
- "person" or "woman" → should return `HEYRA307.png` and the vintner image
