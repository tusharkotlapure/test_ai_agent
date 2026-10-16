
import numpy as np

from devpilot.embeddings import embed_query, embed_texts


def semantic_search(
    chunks: list[dict],
    query: str,
    limit: int = 5,
) -> list[dict]:
    """Rank code chunks by embedding similarity."""
    if not query.strip():
        raise ValueError("Query must not be empty")

    if limit <= 0:
        raise ValueError("Limit must be positive")

    if not chunks:
        return []

    chunk_texts = [chunk["text"] for chunk in chunks]

    chunk_vectors = embed_texts(chunk_texts)
    query_vector = embed_query(query)

    # Embeddings are normalized, so dot product gives cosine similarity.
    scores = np.asarray(chunk_vectors) @ query_vector

    ranked_indices = np.argsort(scores)[::-1][:limit]

    results = []

    for index in ranked_indices:
        result = dict(chunks[int(index)])
        result["score"] = float(scores[index])
        results.append(result)

    return results
