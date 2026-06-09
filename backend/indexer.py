import hashlib
import io
import os
from pathlib import Path
from typing import Optional

import chromadb
from sentence_transformers import SentenceTransformer
from PIL import Image

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".bmp", ".tiff"}
MODEL_NAME = "clip-ViT-B-32"
DEMO_IMAGES_DIR = os.environ.get("DEMO_IMAGES_DIR", "./demo-images")


class ImageIndexer:
    def __init__(self, persist_dir: str = "./data"):
        self.model = SentenceTransformer(MODEL_NAME)
        self.client = chromadb.PersistentClient(path=persist_dir)
        self.collection = self.client.get_or_create_collection(
            name="images",
            metadata={"hnsw:space": "cosine"},
        )
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
            for f in new_files:
                try:
                    img = Image.open(f).convert("RGB")
                    images.append(img)
                    valid_files.append(f)
                except Exception:
                    skipped += 1
                    continue

            if not images:
                continue

            embeddings = self.model.encode(images, batch_size=batch_size)

            ids = []
            metadatas = []
            for f in valid_files:
                img_id = self._image_id(str(f.resolve()))
                ids.append(img_id)
                metadatas.append(
                    {
                        "filename": f.name,
                        "path": str(f.resolve()),
                        "extension": f.suffix.lower(),
                    }
                )

            self.collection.add(
                ids=ids,
                embeddings=embeddings.tolist(),
                metadatas=metadatas,
            )
            indexed += len(valid_files)

        return indexed, skipped

    def search(self, query: str, n_results: int = 20) -> list[dict]:
        if self.collection.count() == 0:
            return []

        text_embedding = self.model.encode([query])
        results = self.collection.query(
            query_embeddings=text_embedding.tolist(),
            n_results=min(n_results, self.collection.count()),
        )

        output = []
        for i, img_id in enumerate(results["ids"][0]):
            metadata = results["metadatas"][0][i]
            distance = results["distances"][0][i]
            score = 1 - distance

            output.append(
                {
                    "id": img_id,
                    "filename": metadata["filename"],
                    "path": metadata["path"],
                    "score": round(score, 4),
                }
            )

        return output

    def get_recent(self, limit: int = 20) -> list[dict]:
        if self.collection.count() == 0:
            return []

        results = self.collection.get(limit=limit, include=["metadatas"])

        output = []
        for i, img_id in enumerate(results["ids"]):
            metadata = results["metadatas"][i]
            output.append(
                {
                    "id": img_id,
                    "filename": metadata["filename"],
                    "path": metadata["path"],
                }
            )

        return output

    def get_random(self, limit: int = 20) -> list[dict]:
        import random

        if self.collection.count() == 0:
            return []

        total = self.collection.count()
        results = self.collection.get(limit=total, include=["metadatas"])

        indices = random.sample(range(len(results["ids"])), min(limit, len(results["ids"])))

        output = []
        for i in indices:
            metadata = results["metadatas"][i]
            output.append(
                {
                    "id": results["ids"][i],
                    "filename": metadata["filename"],
                    "path": metadata["path"],
                }
            )

        return output

    def get_image_path(self, image_id: str) -> Optional[str]:
        results = self.collection.get(ids=[image_id], include=["metadatas"])
        if results["ids"]:
            return results["metadatas"][0]["path"]
        return None

    def total_images(self) -> int:
        return self.collection.count()
