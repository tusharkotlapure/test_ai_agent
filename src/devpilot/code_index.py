
from devpilot.chunking import chunk_text


def index_source_file(
    path: str,
    content: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    """Convert one source file into searchable chunks."""
    chunks = chunk_text(
        content,
        chunk_size=chunk_size,
        overlap=overlap,
    )

    indexed_chunks = []

    for chunk in chunks:
        indexed_chunks.append({
            "path": path,
            "start_line": chunk["start_line"],
            "end_line": chunk["end_line"],
            "text": chunk["text"],
        })

    return indexed_chunks


def search_index(
    chunks: list[dict],
    query: str,
    limit: int = 5,
) -> list[dict]:
    """Rank chunks by the number of query terms they contain."""
    if not query.strip():
        raise ValueError("Query must not be empty")

    if limit <= 0:
        raise ValueError("Limit must be positive")

    terms = set(query.casefold().split())
    scored_chunks = []

    for chunk in chunks:
        text = chunk["text"].casefold()
        score = sum(1 for term in terms if term in text)

        if score > 0:
            scored_chunks.append({
                **chunk,
                "score": score,
            })

    scored_chunks.sort(
        key=lambda item: (
            -item["score"],
            item["path"],
            item["start_line"],
        )
    )

    return scored_chunks[:limit]
