from devpilot.code_index import index_source_file
from devpilot.tools import (
    get_github_repo_info,
    read_github_file,
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
        result = read_github_file(owner, repo, path)
        
        if not result["content"].strip():
            continue
        
        indexed_chunks.extend(
            index_source_file(
                path=result["path"],
                content=result["content"],
            )
        )

    return indexed_chunks
