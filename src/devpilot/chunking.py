def chunk_text(
    text: str,
    chunk_size: int = 80,
    overlap: int = 10,
) -> list[dict]:
    """Split text into overlapping line-based chunks."""

    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")

    if overlap < 0 or overlap >= chunk_size:
        raise ValueError("overlap must be non-negative and less than chunk_size")

    lines = text.splitlines()
    chunks = []
    start = 0

    while start < len(lines):
        end = min(start + chunk_size, len(lines))

        chunks.append(
            {
                "start_line": start + 1,
                "end_line": end,
                "text": "\n".join(lines[start:end]),
            }
        )

        if end == len(lines):
            break

        start = end - overlap

    return chunks
