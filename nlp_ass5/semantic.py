from __future__ import annotations

import hashlib
import json
import os
import re
from dataclasses import dataclass
from pathlib import Path

import numpy as np

from .common import DATA_PROCESSED, clean_text


DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
CACHE_DIR = DATA_PROCESSED / "embedding_cache"


def text_hash(text: str) -> str:
    return hashlib.sha1(text.encode("utf-8", errors="ignore")).hexdigest()


def cache_key(name: str, model_name: str, ids: list[str], texts: list[str]) -> str:
    digest = hashlib.sha1()
    digest.update(model_name.encode("utf-8"))
    digest.update(name.encode("utf-8"))
    for item_id, text in zip(ids, texts):
        digest.update(str(item_id).encode("utf-8", errors="ignore"))
        digest.update(text_hash(text).encode("ascii"))
    return digest.hexdigest()


def chunk_text(text: str, max_words: int = 160, overlap: int = 40) -> list[str]:
    cleaned = clean_text(text)
    if not cleaned:
        return []
    sentences = re.split(r"(?<=[.!?])\s+", cleaned)
    chunks: list[str] = []
    current: list[str] = []
    for sentence in sentences:
        words = sentence.split()
        if not words:
            continue
        if len(current) + len(words) > max_words and current:
            chunks.append(" ".join(current))
            current = current[-overlap:] if overlap else []
        current.extend(words)
    if current:
        chunks.append(" ".join(current))
    return chunks[:80]


@dataclass
class EncodedTexts:
    ids: list[str]
    texts: list[str]
    embeddings: np.ndarray


class SemanticEmbedder:
    def __init__(self, model_name: str | None = None, batch_size: int | None = None) -> None:
        self.model_name = model_name or os.environ.get("UFO_EMBEDDING_MODEL", DEFAULT_MODEL)
        self.batch_size = batch_size or int(os.environ.get("UFO_EMBEDDING_BATCH_SIZE", "128"))
        self.available = False
        self.error = ""
        self.model = None
        try:
            from sentence_transformers import SentenceTransformer

            device = os.environ.get("UFO_EMBEDDING_DEVICE")
            self.model = SentenceTransformer(self.model_name, device=device)
            self.available = True
        except Exception as exc:  # pragma: no cover - depends on optional runtime deps
            self.error = str(exc)

    def encode_cached(self, name: str, ids: list[str], texts: list[str]) -> EncodedTexts:
        CACHE_DIR.mkdir(parents=True, exist_ok=True)
        key = cache_key(name, self.model_name, ids, texts)
        npz_path = CACHE_DIR / f"{name}_{key}.npz"
        meta_path = CACHE_DIR / f"{name}_{key}.json"
        if npz_path.exists() and meta_path.exists():
            embeddings = np.load(npz_path)["embeddings"]
            meta = json.loads(meta_path.read_text(encoding="utf-8"))
            return EncodedTexts(ids=meta["ids"], texts=meta["texts"], embeddings=embeddings)
        if not self.available or self.model is None:
            raise RuntimeError(f"Semantic model unavailable and no matching cache exists: {self.error}")

        embeddings = self.model.encode(
            texts,
            batch_size=self.batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=True,
        ).astype("float32")
        np.savez_compressed(npz_path, embeddings=embeddings)
        meta_path.write_text(json.dumps({"ids": ids, "texts": texts}, ensure_ascii=False), encoding="utf-8")
        return EncodedTexts(ids=ids, texts=texts, embeddings=embeddings)


def cosine_scores(query: np.ndarray, documents: np.ndarray) -> np.ndarray:
    if documents.size == 0:
        return np.array([], dtype="float32")
    return np.maximum(documents @ query, 0.0)
