<p align="center">
  <h1 align="center">img™</h1>
  <p align="center">
    Semantic image search powered by CLIP.<br/>
    Type what you see — find what you mean.
  </p>
</p>

<p align="center">
  <a href="https://github.com/Heyra-Global/img/blob/main/LICENSE"><img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="MIT License"></a>
  <a href="https://github.com/Heyra-Global/img"><img src="https://img.shields.io/badge/python-3.11+-green.svg" alt="Python 3.11+"></a>
  <a href="https://github.com/Heyra-Global/img"><img src="https://img.shields.io/badge/next.js-16-black.svg" alt="Next.js 16"></a>
</p>

---

Search your image library using natural language. Type "sunset over water" and find matching images instantly — no tags, no filenames, just meaning.

## Features

- **Semantic search** — find images by meaning, not filenames
- **Zero configuration** — auto-indexes demo images on first run
- **Multi-select & download** — select images and download as ZIP
- **Instant results** — vector similarity search via ChromaDB
- **Self-hosted** — runs entirely on your machine, no cloud required
- **Beautiful UI** — dark masonry grid with smooth transitions

## Quick Start

> Requires Python 3.11+ and Node.js 18+

### 1. Start the backend

```bash
cd backend
pip install -r requirements.txt
uvicorn main:app --reload
```

On first run, the CLIP model downloads (~350MB) and the 8 included demo images are automatically indexed.

### 2. Start the frontend

```bash
cd frontend
npm install
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) and start searching.

That's it. Three commands to semantic image search.

## How It Works

```
"green nature" → CLIP text encoder → 512-dim vector
                                          ↓
                                    cosine similarity
                                          ↓
              stored image embeddings ← CLIP image encoder ← your images
                                          ↓
                                   ranked results 🎯
```

[CLIP](https://openai.com/research/clip) (Contrastive Language-Image Pre-training) maps images and text into the same vector space. Similar concepts end up close together — so "a red sports car" finds images of red cars even if the filename is `IMG_4392.jpg`.

## Index Your Own Images

Point it at any folder:

```bash
curl -X POST http://localhost:8000/api/index \
  -H "Content-Type: application/json" \
  -d '{"folder": "/path/to/your/images"}'
```

Supports: `.jpg` `.jpeg` `.png` `.webp` `.gif` `.bmp` `.tiff`

Images are deduplicated by path — re-indexing the same folder is safe and fast.

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `IMAGES_DIR` | `./images` | Default folder for indexing |
| `DATA_DIR` | `./data` | ChromaDB persistence directory |
| `DEMO_IMAGES_DIR` | `./demo-images` | Demo images for auto-indexing |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend URL for frontend |

Copy `.env.example` to `.env` and adjust as needed.

## Deployment

### Docker (backend)

```bash
cd backend
docker build -t img-backend .
docker run -p 8000:8000 \
  -v $(pwd)/data:/data \
  -v $(pwd)/../demo-images:/demo-images \
  img-backend
```

### Frontend

Deploy the Next.js app to any host (Vercel, Netlify, Cloudflare Pages, Docker):

```bash
cd frontend
NEXT_PUBLIC_API_URL=https://your-backend.example.com npm run build
```

## API Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/api/search?q=...&limit=20&offset=0` | Semantic search |
| `GET` | `/api/random?limit=20` | Random selection for inspiration |
| `GET` | `/api/recent?limit=20&offset=0` | Recently indexed images |
| `GET` | `/api/images/{id}` | Serve image by ID |
| `GET` | `/api/download-file/{id}` | Download single image |
| `POST` | `/api/download` | Download selected as ZIP |
| `POST` | `/api/index` | Index a folder of images |
| `GET` | `/api/stats` | Collection statistics |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Search model | CLIP ViT-B/32 via sentence-transformers |
| Vector DB | ChromaDB (local, file-based) |
| Backend | Python, FastAPI |
| Frontend | Next.js 16, React 19, TailwindCSS v4 |
| UI components | shadcn/ui |
| Layout | react-masonry-css |

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

```bash
# Fork and clone, then:
cd backend && pip install -r requirements.txt
cd frontend && npm install

# Run both in dev mode and hack away
```

## License

MIT — see [LICENSE](LICENSE).

---

<p align="center">
  Built by <a href="https://github.com/Heyra-Global">Heyra</a>
</p>
