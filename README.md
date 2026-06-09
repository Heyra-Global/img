# img

Semantic image search powered by [CLIP](https://openai.com/research/clip). Search your image library using natural language — type "sunset over water" and find matching images instantly.

![img screenshot](https://github.com/Heyra-Global/img/raw/main/.github/screenshot.png)

## Features

- **Semantic search** — find images by meaning, not filenames
- **Zero configuration** — auto-indexes demo images on first run
- **Multi-select & download** — select images and download as ZIP
- **Fast** — vector similarity search via ChromaDB
- **Self-hosted** — runs entirely on your machine, no cloud required

## Quick Start

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

On first run, the 8 included demo images are automatically indexed.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start searching.

## Index Your Own Images

Place images in any folder and index via the API:

```bash
curl -X POST http://localhost:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"folder": "/path/to/your/images"}'
```

Supported formats: `.jpg`, `.jpeg`, `.png`, `.webp`, `.gif`, `.bmp`, `.tiff`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGES_DIR` | `./images` | Default folder for indexing |
| `DATA_DIR` | `./data` | ChromaDB persistence directory |
| `DEMO_IMAGES_DIR` | `./demo-images` | Demo images for auto-indexing |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |

See `.env.example` for a template.

## Deployment

### Docker

```bash
cd backend
docker build -t img-backend .
docker run -p 8000:8000 -v ./data:/data -v ./demo-images:/demo-images img-backend
```

### Frontend

The Next.js frontend can be deployed to any static host (Vercel, Netlify, Cloudflare Pages):

```bash
cd frontend
npm run build
```

Set `NEXT_PUBLIC_API_URL` to your backend URL at build time.

## Tech Stack

- **Backend:** Python, FastAPI, sentence-transformers (CLIP), ChromaDB
- **Frontend:** Next.js, React, TailwindCSS, shadcn/ui
- **Search:** CLIP ViT-B/32 for joint text-image embeddings
- **Vector DB:** ChromaDB (local, file-based)

## API

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search?q=...&limit=20&offset=0` | Semantic search |
| `GET` | `/api/random?limit=20` | Random images |
| `GET` | `/api/recent?limit=20&offset=0` | Recently indexed |
| `GET` | `/api/images/{id}` | Serve image by ID |
| `GET` | `/api/download-file/{id}` | Download single image |
| `POST` | `/api/download` | Download multiple as ZIP |
| `POST` | `/api/index` | Index a folder |
| `GET` | `/api/stats` | Collection statistics |

## License

MIT — see [LICENSE](LICENSE).
