# img MCP Server

An MCP (Model Context Protocol) server that exposes semantic image search to AI assistants. Any MCP-compatible client (Cursor, Claude Desktop, Claude Code, etc.) can search your image library using natural language.

## Tools

| Tool | Description |
|------|-------------|
| `search_images` | Find images by meaning — "green nature", "person at desk", "red abstract" |
| `get_random_images` | Browse random images for inspiration |
| `copy_image_to` | Copy a found image to a destination folder (e.g. `media/` in a slides project) |
| `index_folder` | Index a folder of images for search |
| `get_stats` | Check how many images are indexed |

## Setup

### 1. Install dependencies

```bash
cd mcp-server
pip install -r requirements.txt
```

The first run downloads the CLIP model (~350MB).

### 2. Configure your MCP client

#### Cursor

Add to your Cursor MCP settings (`.cursor/mcp.json` in your project or global settings):

```json
{
  "mcpServers": {
    "img": {
      "command": "python",
      "args": ["/absolute/path/to/img/mcp-server/server.py"],
      "env": {
        "DATA_DIR": "/absolute/path/to/img/backend/data",
        "DEMO_IMAGES_DIR": "/absolute/path/to/img/demo-images"
      }
    }
  }
}
```

#### Claude Desktop

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows):

```json
{
  "mcpServers": {
    "img": {
      "command": "python",
      "args": ["/absolute/path/to/img/mcp-server/server.py"],
      "env": {
        "DATA_DIR": "/absolute/path/to/img/backend/data",
        "DEMO_IMAGES_DIR": "/absolute/path/to/img/demo-images"
      }
    }
  }
}
```

#### Claude Code

```bash
claude mcp add img -- python /absolute/path/to/img/mcp-server/server.py
```

### 3. Index your images

Either:
- Let it auto-index the included demo images (happens on first use if DB is empty)
- Use the `index_folder` tool to point at your own images
- Or run the backend separately to index via the API

## Usage Examples

Once configured, just ask your AI assistant:

- "Find me images with green tones"
- "Search for a minimal product shot"
- "Copy that image to my slides media folder"
- "Index all images in ~/Pictures/project-assets"
- "How many images do I have indexed?"

## Example: Slides Integration

Works great with [noskillish/slides](https://github.com/noskillish/slides):

1. Ask your AI assistant to find an image: "Find a dramatic red background image"
2. The agent calls `search_images("dramatic red abstract")`
3. You pick one from the results
4. The agent calls `copy_image_to(id, "./media/", "red-bg.png")`
5. The agent writes the slide HTML: `<img src="media/red-bg.png">`

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `DATA_DIR` | `../backend/data` | ChromaDB persistence directory |
| `DEMO_IMAGES_DIR` | `../demo-images` | Demo images for auto-indexing |
| `BACKEND_DIR` | `../backend` | Path to backend (for importing ImageIndexer) |

## How It Works

The server imports `ImageIndexer` directly from the backend — no HTTP needed. When an AI tool is called, it encodes the query with CLIP and searches the local ChromaDB vector database. Results include absolute file paths so the agent can read, copy, or reference images.
