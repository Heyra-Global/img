"""
img MCP Server — semantic image search for AI agents.

Exposes CLIP-based image search as MCP tools so any AI assistant
can find and retrieve images by meaning.
"""

import os
import shutil
import sys
from pathlib import Path

from mcp.server.fastmcp import FastMCP

# Add the backend directory to the path so we can import ImageIndexer
BACKEND_DIR = os.environ.get("BACKEND_DIR", str(Path(__file__).parent.parent / "backend"))
sys.path.insert(0, BACKEND_DIR)

from indexer import ImageIndexer

DATA_DIR = os.environ.get("DATA_DIR", str(Path(__file__).parent.parent / "backend" / "data"))
DEMO_IMAGES_DIR = os.environ.get("DEMO_IMAGES_DIR", str(Path(__file__).parent.parent / "demo-images"))

os.environ.setdefault("DEMO_IMAGES_DIR", DEMO_IMAGES_DIR)

mcp = FastMCP(
    "img",
    description="Semantic image search powered by CLIP. Find images by meaning, not filenames.",
)

indexer: ImageIndexer | None = None


def _get_indexer() -> ImageIndexer:
    global indexer
    if indexer is None:
        indexer = ImageIndexer(persist_dir=DATA_DIR)
    return indexer


@mcp.tool()
def search_images(query: str, limit: int = 10) -> list[dict]:
    """Search for images using natural language. Returns images ranked by semantic similarity.

    Use this to find images matching a description, mood, color, or concept.
    Examples: "green nature", "person presenting", "minimal product shot", "red abstract".

    Args:
        query: Natural language description of the image you're looking for.
        limit: Maximum number of results to return (default 10, max 50).
    """
    limit = min(max(1, limit), 50)
    idx = _get_indexer()
    results = idx.search(query, n_results=limit)
    return results


@mcp.tool()
def get_random_images(limit: int = 8) -> list[dict]:
    """Get a random selection of indexed images for browsing and inspiration.

    Useful when you want to see what's available without a specific query.

    Args:
        limit: Number of random images to return (default 8, max 50).
    """
    limit = min(max(1, limit), 50)
    idx = _get_indexer()
    return idx.get_random(limit)


@mcp.tool()
def copy_image_to(image_id: str, destination: str, rename: str = "") -> dict:
    """Copy an image from the indexed collection to a destination folder.

    This is the key integration tool — use it to place images into project
    folders like media/ in a slides repo, or assets/ in a web project.

    Args:
        image_id: The image ID from a search or random result.
        destination: Target directory path (absolute or relative to cwd).
        rename: Optional new filename. If empty, keeps the original name.
    """
    idx = _get_indexer()
    source_path = idx.get_image_path(image_id)

    if not source_path or not Path(source_path).exists():
        return {"error": f"Image not found for id: {image_id}"}

    dest_dir = Path(destination).resolve()
    if not dest_dir.exists():
        dest_dir.mkdir(parents=True, exist_ok=True)

    source = Path(source_path)
    filename = rename if rename else source.name
    dest_file = dest_dir / filename

    shutil.copy2(source, dest_file)

    return {
        "source": str(source),
        "destination": str(dest_dir),
        "copied_to": str(dest_file),
        "filename": filename,
    }


@mcp.tool()
def index_folder(folder: str) -> dict:
    """Index all images in a folder (recursively) for semantic search.

    Scans for .jpg, .jpeg, .png, .webp, .gif, .bmp, .tiff files.
    Already-indexed images are skipped automatically.

    Args:
        folder: Absolute path to the folder containing images.
    """
    folder_path = Path(folder).resolve()
    if not folder_path.exists():
        return {"error": f"Folder not found: {folder}"}

    idx = _get_indexer()
    indexed, skipped = idx.index_folder(str(folder_path))

    return {
        "indexed": indexed,
        "skipped": skipped,
        "total": idx.total_images(),
        "folder": str(folder_path),
    }


@mcp.tool()
def get_stats() -> dict:
    """Get statistics about the indexed image collection.

    Returns the total number of indexed images and the data directory path.
    """
    idx = _get_indexer()
    return {
        "total_images": idx.total_images(),
        "data_dir": DATA_DIR,
        "demo_images_dir": DEMO_IMAGES_DIR,
    }


if __name__ == "__main__":
    mcp.run()
