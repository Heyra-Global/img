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
├── mcp-server/
│   ├── server.py         # MCP server (same search, no HTTP needed)
│   ├── requirements.txt
│   └── README.md
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

## MCP Server

The `mcp-server/` directory contains a standalone MCP server that exposes the same search functionality to AI agents (Cursor, Claude Desktop, Claude Code) without needing the FastAPI backend.

### Tools available via MCP

| Tool | Purpose |
|------|---------|
| `search_images` | Semantic search by natural language query |
| `get_random_images` | Random selection for browsing |
| `copy_image_to` | Copy image to a destination folder (e.g. slides `media/`) |
| `index_folder` | Index a new folder of images |
| `get_stats` | Collection statistics |

### Integration with slides (noskillish/slides)

The MCP server is designed to compose with other tools. Example workflow:

1. Agent calls `search_images("dramatic sunset")` → gets results with file paths
2. Agent calls `copy_image_to(id, "./media/", "sunset.png")` → image copied to slides project
3. Agent writes the HTML slide referencing `media/sunset.png`

### Running the MCP server

```bash
cd mcp-server
pip install -r requirements.txt
python server.py  # runs via stdio
```

Or configure in your MCP client (see `mcp-server/README.md` for Cursor/Claude Desktop config).

## Testing Search Quality

The demo images are chosen to validate semantic search:
- "green" → should return `HEYRA423.png` and the green grapes image
- "red" → should return `HEYRA168.png` and the red grape clusters
- "wine" or "glass" → should return the minimalist wine study
- "person" or "woman" → should return `HEYRA307.png` and the vintner image
