
from devpilot.code_index import index_source_file
from devpilot.tools import (
    get_github_repo_info,
    read_github_file,
)


def index_repository_file(
    owner: str,
    repo: str,
    path: str,
) -> list[dict]:
    """Read and index a single GitHub file."""
    result = read_github_file(owner, repo, path)
    content = result["content"]

    if not content.strip():
        return []

    return index_source_file(
        path=result["path"],
        content=content,
    )


def build_repository_index(
    owner: str,
    repo: str,
    paths: list[str],
) -> list[dict]:
    """Build an in-memory index from explicitly selected GitHub files."""
    get_github_repo_info(owner, repo)

    indexed_chunks = []

    for path in paths:
        indexed_chunks.extend(
            index_repository_file(owner, repo, path)
        )

    return indexed_chunks
