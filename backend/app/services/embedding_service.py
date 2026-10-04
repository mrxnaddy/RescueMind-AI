import threading
from typing import Any

import numpy as np

from app.config import settings


class EmbeddingError(Exception):
    """Raised when the embedding model cannot load or run."""


_model: Any = None
_lock = threading.Lock()


def get_model_name() -> str:
    return settings.EMBEDDING_MODEL


def _get_model() -> Any:
    """Load the model once (the first call downloads it)."""

    global _model

    if _model is None:
        with _lock:
            if _model is None:
                try:
                    from fastembed import TextEmbedding

                    _model = TextEmbedding(model_name=settings.EMBEDDING_MODEL)
                except Exception as exc:
                    raise EmbeddingError(
                        "Could not load embedding model "
                        f"'{settings.EMBEDDING_MODEL}': {exc}"
                    ) from exc

    return _model


def embed_texts(texts: list[str]) -> list[list[float]]:
    cleaned = [text.strip() for text in texts]

    if not cleaned or any(not text for text in cleaned):
        raise EmbeddingError("Cannot embed empty text")

    model = _get_model()

    try:
        vectors = list(model.embed(cleaned))
    except Exception as exc:
        raise EmbeddingError(f"Embedding failed: {exc}") from exc

    return [np.asarray(vector, dtype=float).tolist() for vector in vectors]


def embed_text(text: str) -> list[float]:
    return embed_texts([text])[0]


def cosine_similarity(a: list[float], b: list[float]) -> float:
    vector_a = np.asarray(a, dtype=float)
    vector_b = np.asarray(b, dtype=float)

    denominator = np.linalg.norm(vector_a) * np.linalg.norm(vector_b)

    if denominator == 0:
        return 0.0

    return float(np.dot(vector_a, vector_b) / denominator)