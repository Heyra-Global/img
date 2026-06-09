# Frontend Agent Guide

## Overview

Next.js 16 app with App Router, TailwindCSS v4, and shadcn/ui components. Dark theme with a masonry image grid and real-time semantic search.

## Stack

- **Next.js 16** (App Router, React 19)
- **TailwindCSS v4** (via `@tailwindcss/postcss`)
- **shadcn/ui** — component primitives (`button`, `input`, `badge`, `skeleton`, `dialog`)
- **react-masonry-css** — stable masonry layout
- **lucide-react** — icons

## File Map

```
src/
├── app/
│   ├── layout.tsx      # Root layout, fonts, dark mode
│   ├── page.tsx        # Main page — search, grid, infinite scroll
│   ├── globals.css     # Tailwind imports, masonry CSS, theme vars
│   └── favicon.ico
├── components/
│   ├── search-bar.tsx  # Search input with loading indicator
│   ├── image-grid.tsx  # Masonry grid wrapper
│   ├── image-card.tsx  # Individual image card (hover actions, select, download)
│   ├── selection-bar.tsx # Multi-select bottom bar (download ZIP, clear)
│   └── ui/             # shadcn/ui primitives
├── lib/
│   ├── api.ts          # API client (search, random, download, index, stats)
│   └── utils.ts        # cn() helper for classnames
```

## Key Patterns

### Data Flow

1. `page.tsx` manages all state (images, query, selection, pagination)
2. On mount: fetches random images via `getRandomImages()`
3. On query change: debounced 300ms search via `searchImages()`
4. Infinite scroll: `IntersectionObserver` via callback ref triggers `loadMore()`
5. State updates wrapped in `startTransition()` for smooth UI

### API Client (`lib/api.ts`)

All backend calls go through typed functions. The base URL is `NEXT_PUBLIC_API_URL` (defaults to `http://localhost:8000`).

### Image Loading

- Images use `loading="lazy"` for viewport-based loading
- Fade-in transition on load (`opacity-0` → `opacity-100`)
- Masonry layout prevents reflow when new images appear

### Multi-Select

- User clicks select icon on cards → adds to `selected` Set
- `SelectionBar` appears at bottom with count + download ZIP action
- ZIP download via `POST /api/download` with selected IDs

## Running

```bash
npm install
npm run dev          # http://localhost:3000
npm run build        # production build
npm run lint         # ESLint
```

## Environment

| Variable | Default | Description |
|----------|---------|-------------|
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | Backend API base URL |

## Styling Notes

- Dark mode only (hardcoded `dark` class on `<html>`)
- CSS variables for theming in `globals.css`
- Floating header with backdrop blur
- Masonry grid uses custom CSS classes (`.masonry-grid`, `.masonry-grid-column`)
