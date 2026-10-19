
import time

from devpilot.repository_index import (
    build_repository_index,
    index_repository_file,
)

# Repository-level cache: creation time and combined chunks.
_INDEX_CACHE: dict[tuple, tuple[float, list[dict]]] = {}

# Per-file cache: (GitHub SHA, indexed chunks).
_FILE_CACHE: dict[tuple[str, str, str], tuple[str, list[dict]]] = {}

CACHE_TTL_SECONDS = 300


def get_repository_index(
    owner: str,
    repo: str,
    paths: list[str],
    refresh: bool = False,
    file_shas: dict[str, str] | None = None,
) -> list[dict]:
    """Return a cached index, incrementally updating changed files."""
    owner_key = owner.casefold()
    repo_key = repo.casefold()

    cache_key = (
        owner_key,
        repo_key,
        tuple(sorted(paths)),
    )

    cached_entry = _INDEX_CACHE.get(cache_key)

    if not refresh and cached_entry is not None:
        created_at, cached_chunks = cached_entry

        if time.monotonic() - created_at < CACHE_TTL_SECONDS:
            return cached_chunks

    # Preserve the existing full-rebuild behavior for callers
    # that do not provide GitHub file SHAs.
    if file_shas is None:
        chunks = build_repository_index(owner, repo, paths)
    else:
        chunks = []

        for path in paths:
            sha = file_shas.get(path)

            if sha is None:
                raise ValueError(f"Missing GitHub SHA for {path}")

            file_key = (owner_key, repo_key, path)
            cached_file = _FILE_CACHE.get(file_key)

            if cached_file is not None and cached_file[0] == sha:
                file_chunks = cached_file[1]
            else:
                file_chunks = index_repository_file(owner, repo, path)
                _FILE_CACHE[file_key] = (sha, file_chunks)

            chunks.extend(file_chunks)

        # Remove cached files that are no longer selected.
        selected_paths = set(paths)

        for file_key in list(_FILE_CACHE):
            if file_key[:2] == (owner_key, repo_key):
                if file_key[2] not in selected_paths:
                    del _FILE_CACHE[file_key]

    _INDEX_CACHE[cache_key] = (time.monotonic(), chunks)
    return chunks


def clear_index_cache() -> None:
    """Clear all repository and per-file index caches."""
    _INDEX_CACHE.clear()
    _FILE_CACHE.clear()
