
from collections import OrderedDict

import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"
MAX_EMBEDDING_CACHE_SIZE = 1000

_model = None
_EMBEDDING_CACHE: OrderedDict[str, np.ndarray] = OrderedDict()


def get_embedding_model() -> SentenceTransformer:
    global _model

    if _model is None:
        _model = SentenceTransformer(MODEL_NAME)

    return _model


def embed_texts(texts: list[str]) -> np.ndarray:
    if not texts:
        return np.array([])

    missing_texts = list(
        dict.fromkeys(
            text for text in texts
            if text not in _EMBEDDING_CACHE
        )
    )

    if missing_texts:
        model = get_embedding_model()
        embeddings = model.encode(
            missing_texts,
            normalize_embeddings=True,
            convert_to_numpy=True,
        )

        for text, embedding in zip(missing_texts, embeddings):
            _EMBEDDING_CACHE[text] = embedding
            _EMBEDDING_CACHE.move_to_end(text)

            # Remove the least recently used embedding if over capacity.
            while len(_EMBEDDING_CACHE) > MAX_EMBEDDING_CACHE_SIZE:
                _EMBEDDING_CACHE.popitem(last=False)

    # Mark cached entries as recently used.
    for text in texts:
        _EMBEDDING_CACHE.move_to_end(text)

    return np.stack([_EMBEDDING_CACHE[text] for text in texts])


def embed_query(query: str) -> np.ndarray:
    if not query.strip():
        raise ValueError("Query must not be empty")

    return embed_texts([query])[0]


def clear_embedding_cache() -> None:
    _EMBEDDING_CACHE.clear()
