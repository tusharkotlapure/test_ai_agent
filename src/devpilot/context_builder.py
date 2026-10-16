
def deduplicate_chunks(chunks: list[dict]) -> list[dict]:
    """Remove overlapping lines while preserving original line numbers."""
    seen_lines: dict[str, set[int]] = {}
    deduplicated = []

    for chunk in chunks:
        path = chunk["path"]
        start_line = chunk["start_line"]
        file_seen = seen_lines.setdefault(path, set())

        unique_lines = []

        for offset, line in enumerate(chunk["text"].splitlines()):
            line_number = start_line + offset

            if line_number not in file_seen:
                unique_lines.append((line_number, line))
                file_seen.add(line_number)

        if not unique_lines:
            continue

        deduplicated.append({
            **chunk,
            "text": "\n".join(line for _, line in unique_lines),
            "line_numbers": [number for number, _ in unique_lines],
        })

    return deduplicated
