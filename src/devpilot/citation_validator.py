import re

_CITATION_PATTERNS = [
    re.compile(
        r"(?P<path>(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+)"
        r":(?P<start>\d+)(?:-(?P<end>\d+))?"
    ),
    re.compile(
        r"(?P<path>(?:[\w.-]+/)*[\w.-]+\.[A-Za-z0-9]+)"
        r"[\s`*]*(?:\*\*)?[^ \n]{0,10}?"
        r"[\s`*(),]*(?:lines?\s+)"
        r"[\s`*]*(?P<start>\d+)"
        r"(?:\s*-\s*(?P<end>\d+))?",
        re.IGNORECASE,
    ),
]


def extract_citations(answer: str) -> list[dict]:
    """Extract supported compact and natural-language citations."""
    citations = []
    seen = set()

    for pattern in _CITATION_PATTERNS:
        for match in pattern.finditer(answer):
            path = match.group("path")
            start = int(match.group("start"))
            end = int(match.group("end") or start)

            key = (path, start, end)
            if key in seen:
                continue

            seen.add(key)
            citations.append(
                {
                    "path": path,
                    "start_line": start,
                    "end_line": end,
                }
            )

    return citations


def validate_citations(
    answer: str,
    context_chunks: list[dict],
) -> dict:
    """Validate file and line citations against retrieved source context."""
    available_lines: dict[str, set[int]] = {}

    for chunk in context_chunks:
        path = chunk["path"]

        if "line_numbers" in chunk:
            lines = set(chunk["line_numbers"])
        else:
            lines = set(
                range(
                    chunk["start_line"],
                    chunk["end_line"] + 1,
                )
            )

        available_lines.setdefault(path, set()).update(lines)

    citations = []

    for citation in extract_citations(answer):
        path = citation["path"]
        start = citation["start_line"]
        end = citation["end_line"]

        valid = (
            start <= end
            and path in available_lines
            and all(line in available_lines[path] for line in range(start, end + 1))
        )

        citations.append(
            {
                **citation,
                "valid": valid,
            }
        )

    return {
        "is_valid": all(item["valid"] for item in citations),
        "citations": citations,
        "has_citations": bool(citations),
    }
