"""
Semantic search layer.

Converts all intent variants into embeddings (sentence-transformers),
builds a FAISS index, and retrieves the top-k most similar intents
for a given user query.

Embeddings are cached to disk so they're only computed once.
"""

from __future__ import annotations

import os
import pickle
from pathlib import Path

import numpy as np

from config import EMBEDDING_MODEL, EMBEDDINGS_CACHE, SEMANTIC_TOP_K
from knowledge_base import INTENTS
from preprocessor import normalize

# ── Lazy imports (heavy) ──────────────────────────────────────────────────────
_model = None
_index = None
_meta: list[str] = []  # parallel list: index row → intent name


def _load_model():
    global _model
    if _model is None:
        from sentence_transformers import SentenceTransformer
        _model = SentenceTransformer(EMBEDDING_MODEL)
    return _model


def _build_index(embeddings: np.ndarray):
    import faiss
    d = embeddings.shape[1]
    index = faiss.IndexFlatIP(d)  # Inner product (cosine after L2 norm)
    faiss.normalize_L2(embeddings)
    index.add(embeddings)
    return index


def _gather_corpus() -> tuple[list[str], list[str]]:
    """Return (texts, intent_names) for every variant in the knowledge base."""
    texts, names = [], []
    for intent in INTENTS:
        for variant in intent["variants"]:
            texts.append(normalize(variant))
            names.append(intent["name"])
    return texts, names


def _load_or_build_cache() -> tuple:
    cache_path = Path(EMBEDDINGS_CACHE)

    if cache_path.exists():
        with open(cache_path, "rb") as f:
            cached = pickle.load(f)
        return cached["embeddings"], cached["meta"]

    model = _load_model()
    texts, names = _gather_corpus()
    embeddings = model.encode(texts, convert_to_numpy=True, show_progress_bar=True)
    embeddings = embeddings.astype("float32")

    cache_path.parent.mkdir(parents=True, exist_ok=True)
    with open(cache_path, "wb") as f:
        pickle.dump({"embeddings": embeddings, "meta": names}, f)

    return embeddings, names


def initialize():
    """Build or load the FAISS index. Call once at startup."""
    global _index, _meta
    embeddings, meta = _load_or_build_cache()
    _meta = meta
    _index = _build_index(embeddings.copy())
    return True


def search(user_input: str, top_k: int = SEMANTIC_TOP_K) -> dict[str, float]:
    """
    Return {intent_name: score (0-100)} for the top-k most similar intents.
    """
    if _index is None:
        return {}

    import faiss
    model = _load_model()
    norm_input = normalize(user_input)
    query_vec = model.encode([norm_input], convert_to_numpy=True).astype("float32")
    faiss.normalize_L2(query_vec)

    distances, indices = _index.search(query_vec, top_k * 3)

    # Aggregate by intent: keep highest score per intent
    scores: dict[str, float] = {}
    for dist, idx in zip(distances[0], indices[0]):
        if idx == -1:
            continue
        name = _meta[idx]
        score = float(dist) * 100  # cosine similarity → 0-100
        if name not in scores or score > scores[name]:
            scores[name] = round(score, 2)

    return scores


def is_ready() -> bool:
    return _index is not None
