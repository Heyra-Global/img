import hashlib
import io
import os
import threading
from collections import OrderedDict
from pathlib import Path
from typing import Optional

# Cap math-library threads BEFORE torch/numpy are imported. In a container with
# a small CPU quota but many visible host cores, the default thread count causes
# severe oversubscription that can make CLIP inference 10-50x slower. Set this
# to the container's vCPU allotment (override via TORCH_NUM_THREADS).
_THREADS = os.environ.get("TORCH_NUM_THREADS", "2")
os.environ.setdefault("OMP_NUM_THREADS", _THREADS)
os.environ.setdefault("MKL_NUM_THREADS", _THREADS)
os.environ.setdefault("OPENBLAS_NUM_THREADS", _THREADS)
os.environ.setdefault("NUMEXPR_NUM_THREADS", _THREADS)

import chromadb
import torch
from sentence_transformers import SentenceTransformer
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
MODEL_NAME = "clip-ViT-B-32"
DEMO_IMAGES_DIR = os.environ.get("DEMO_IMAGES_DIR", "./demo-images")
EMBED_CACHE_SIZE = 1024


class ImageIndexer:
    def __init__(self, persist_dir: str = "./data"):
        try:
            torch.set_num_threads(int(_THREADS))
        except Exception:
            pass
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="images",
            metadata={"hnsw:space": "cosine"},
        )
        # Text-embedding computation is the dominant cost of a search; cache it
        # so repeated/popular queries skip the model entirely.
        self._embed_cache: "OrderedDict[str, list]" = OrderedDict()
        self._embed_lock = threading.Lock()
        self._auto_index_demo_images()

    def _auto_index_demo_images(self):
        """Auto-index demo images on startup if the database is empty."""
        if self.collection.count() > 0:
            return

        demo_path = Path(DEMO_IMAGES_DIR)
        if not demo_path.exists():
            return

        image_files = [f for f in demo_path.rglob("*") if self._is_image(f)]
        if not image_files:
            return

        print(f"[img] Auto-indexing {len(image_files)} demo images from {demo_path}...")
        indexed, skipped = self.index_folder(str(demo_path.resolve()))
        print(f"[img] Indexed {indexed} images ({skipped} skipped)")

    def _image_id(self, path: str) -> str:
        return hashlib.md5(path.encode()).hexdigest()

    def _is_image(self, path: Path) -> bool:
        return path.suffix.lower() in SUPPORTED_EXTENSIONS

    @staticmethod
    def _orientation(width: int, height: int) -> str:
        if width > height:
            return "horizontal"
        if height > width:
            return "vertical"
        return "square"

    def _encode_query(self, query: str) -> list:
        key = query.strip().lower()
        with self._embed_lock:
            cached = self._embed_cache.get(key)
            if cached is not None:
                self._embed_cache.move_to_end(key)
                return cached

        embedding = self.model.encode([query]).tolist()

        with self._embed_lock:
            self._embed_cache[key] = embedding
            self._embed_cache.move_to_end(key)
            while len(self._embed_cache) > EMBED_CACHE_SIZE:
                self._embed_cache.popitem(last=False)
        return embedding

    def warm_queries(self, queries: list[str]) -> None:
        """Pre-compute embeddings for common queries so the first real search
        for each term is instant instead of paying the full encode cost."""
        for q in queries:
            try:
                self._encode_query(q)
            except Exception:
                continue

    def index_folder(self, folder: str, limit: Optional[int] = None) -> tuple:
        folder_path = Path(folder)
        image_files = sorted(
            [f for f in folder_path.rglob("*") if self._is_image(f)],
            key=lambda f: f.name,
        )

        if limit:
            image_files = image_files[:limit]

        existing_ids = set(self.collection.get()["ids"])

        indexed = 0
        skipped = 0
        batch_size = 32

        for i in range(0, len(image_files), batch_size):
            batch_files = image_files[i : i + batch_size]
            new_files = []

            for f in batch_files:
                img_id = self._image_id(str(f.resolve()))
                if img_id in existing_ids:
                    skipped += 1
                else:
                    new_files.append(f)

            if not new_files:
                continue

            images = []
            valid_files = []
            dimensions = []
            for f in new_files:
                try:
                    img = Image.open(f).convert("RGB")
                    images.append(img)
                    valid_files.append(f)
                    dimensions.append(img.size)
                except Exception:
                    skipped += 1
                    continue

            if not images:
                continue

            embeddings = self.model.encode(images, batch_size=batch_size)

            ids = []
            metadatas = []
            for f, (width, height) in zip(valid_files, dimensions):
                img_id = self._image_id(str(f.resolve()))
                ids.append(img_id)
                metadatas.append(
                    {
                        "filename": f.name,
                        "path": str(f.resolve()),
                        "extension": f.suffix.lower(),
                        "width": width,
                        "height": height,
                        "orientation": self._orientation(width, height),
                    }
                )

            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
            )
            indexed += len(valid_files)

        return indexed, skipped

    @staticmethod
    def _where(orientation: Optional[str]) -> Optional[dict]:
        if orientation in ("horizontal", "vertical", "square"):
            return {"orientation": orientation}
        return None

    @staticmethod
    def _row(img_id: str, metadata: dict, score: Optional[float] = None) -> dict:
        row = {
            "id": img_id,
            "filename": metadata["filename"],
            "path": metadata["path"],
            "orientation": metadata.get("orientation"),
            "width": metadata.get("width"),
            "height": metadata.get("height"),
        }
        if score is not None:
            row["score"] = round(score, 4)
        return row

    def search(
        self, query: str, n_results: int = 20, orientation: Optional[str] = None
    ) -> list[dict]:
        if self.collection.count() == 0:
            return []

        text_embedding = self._encode_query(query)
        results = self.collection.query(
            query_embeddings=text_embedding,
            n_results=min(n_results, self.collection.count()),
            where=self._where(orientation),
        )

        output = []
        for i, img_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            output.append(self._row(img_id, metadata, score=1 - distance))

        return output

    def get_recent(self, limit: int = 20, orientation: Optional[str] = None) -> list[dict]:
        if self.collection.count() == 0:
            return []

        results = self.collection.get(
            limit=limit, where=self._where(orientation), include=["metadatas"]
        )

        return [
            self._row(img_id, results["metadatas"][i])
            for i, img_id in enumerate(results["ids"])
        ]

    def get_random(self, limit: int = 20, orientation: Optional[str] = None) -> list[dict]:
        import random

        if self.collection.count() == 0:
            return []

        results = self.collection.get(
            where=self._where(orientation), include=["metadatas"]
        )

        ids = results["ids"]
        if not ids:
            return []

        indices = random.sample(range(len(ids)), min(limit, len(ids)))
        return [self._row(ids[i], results["metadatas"][i]) for i in indices]

    def backfill_orientation(self) -> int:
        """Compute and store orientation/dimensions for images missing it.

        Safe to run on every startup; once all images are tagged it is a no-op.
        """
        if self.collection.count() == 0:
            return 0

        results = self.collection.get(include=["metadatas"])
        ids = results["ids"]
        metadatas = results["metadatas"]

        update_ids = []
        update_metadatas = []
        for img_id, metadata in zip(ids, metadatas):
            if metadata.get("orientation"):
                continue
            path = metadata.get("path", "")
            if not path or not Path(path).exists():
                continue
            try:
                with Image.open(path) as img:
                    width, height = img.size
            except Exception:
                continue
            new_metadata = dict(metadata)
            new_metadata["width"] = width
            new_metadata["height"] = height
            new_metadata["orientation"] = self._orientation(width, height)
            update_ids.append(img_id)
            update_metadatas.append(new_metadata)

        for i in range(0, len(update_ids), 256):
            self.collection.update(
                ids=update_ids[i : i + 256],
                metadatas=update_metadatas[i : i + 256],
            )

        return len(update_ids)

    def get_image_path(self, image_id: str) -> Optional[str]:
        results = self.collection.get(ids=[image_id], include=["metadatas"])
        if results["ids"]:
            return results["metadatas"][0]["path"]
        return None

    def total_images(self) -> int:
        return self.collection.count()
