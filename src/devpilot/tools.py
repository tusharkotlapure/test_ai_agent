import base64
from pathlib import Path
from urllib.parse import quote
from typing import Any
import re
import httpx
from devpilot.config import DEVPILOT_PROJECT_ROOT, GITHUB_TOKEN

IGNORED_ENTRIES = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    ".pytest_cache",
    ".env",
    ".env.local",
    ".env.production",
    ".DS_Store",
}

MAX_ENTRIES = 100


def get_project_info() -> dict[str, str]:
    """Return basic information about DevPilot."""
    return {
        "name": "DevPilot",
        "purpose": "AI assistant for software developers",
        "language": "Python",
        "current_milestone": "Multiple tools and safe filesystem access",
    }


def list_project_files(path: str = ".") -> dict[str, Any]:
    """List files and directories under the configured project root."""
    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    root = DEVPILOT_PROJECT_ROOT
    requested_path = (root / path).resolve()

    # Prevent access outside the configured project root.
    if not requested_path.is_relative_to(root):
        raise ValueError("Access outside the configured project root is denied")

    if not requested_path.is_dir():
        raise ValueError("The requested path is not a directory")

    entries = []

    for entry in sorted(requested_path.iterdir(), key=lambda item: item.name.lower()):
        if entry.name in IGNORED_ENTRIES:
            continue

        # Do not follow symlinks; they may point outside the allowed directory.
        if entry.is_symlink():
            continue

        entries.append(
            {
                "name": entry.name,
                "type": "directory" if entry.is_dir() else "file",
            }
        )

        if len(entries) >= MAX_ENTRIES:
            break

    return {
        "path": str(requested_path.relative_to(root)) or ".",
        "entries": entries,
        "count": len(entries),
        "truncated": len(entries) == MAX_ENTRIES,
    }


GITHUB_API_BASE = "https://api.github.com"
GITHUB_TIMEOUT = 10.0


def github_request(path: str) -> dict | list:
    """Make a read-only request to a GitHub API endpoint."""
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }

    if GITHUB_TOKEN:
        headers["Authorization"] = f"Bearer {GITHUB_TOKEN}"

    response = httpx.get(
        f"{GITHUB_API_BASE}{path}",
        headers=headers,
        timeout=GITHUB_TIMEOUT,
        follow_redirects=False,
    )

    if response.status_code == 404:
        raise ValueError(
            "GitHub repository or resource not found, " "or access is not authorized."
        )

    if response.status_code == 403:
        raise RuntimeError(
            f"GitHub denied the request. " f"Response: {response.text[:1000]}"
        )

    response.raise_for_status()
    return response.json()


def validate_repository(owner: str, repo: str) -> None:
    """Validate individual GitHub owner and repository names."""
    if not isinstance(owner, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", owner):
        raise ValueError("Invalid GitHub owner name")

    if not isinstance(repo, str) or not re.fullmatch(r"[A-Za-z0-9_.-]+", repo):
        raise ValueError("Invalid GitHub repository name")


def get_github_repo_info(owner: str, repo: str) -> dict:
    """Get metadata for a public or authorized GitHub repository."""
    validate_repository(owner, repo)

    data = github_request(f"/repos/{owner}/{repo}")

    return {
        "full_name": data["full_name"],
        "description": data["description"],
        "html_url": data["html_url"],
        "default_branch": data["default_branch"],
        "private": data["private"],
        "language": data["language"],
        "stars": data["stargazers_count"],
    }


def list_github_files(
    owner: str,
    repo: str,
    path: str = ".",
) -> dict:
    """List files and directories at a repository path."""
    validate_repository(owner, repo)

    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    if "\\" in path or path.startswith("/"):
        raise ValueError("Use a relative GitHub repository path")

    segments = [] if path in ("", ".") else path.split("/")

    if any(segment in ("", ".", "..") for segment in segments):
        raise ValueError("Invalid repository path")

    encoded_path = "/".join(quote(segment, safe="") for segment in segments)

    endpoint = f"/repos/{owner}/{repo}/contents"
    if encoded_path:
        endpoint += f"/{encoded_path}"

    data = github_request(endpoint)

    if not isinstance(data, list):
        raise ValueError("The requested path is not a directory")

    entries = [
        {
            "name": item["name"],
            "path": item["path"],
            "type": item["type"],
        }
        for item in data[:100]
    ]

    return {
        "repository": f"{owner}/{repo}",
        "path": path,
        "entries": entries,
        "count": len(entries),
        "truncated": len(data) > 100,
    }


MAX_GITHUB_FILE_BYTES = 100_000


def read_github_file(owner: str, repo: str, path: str) -> dict:
    """Read a text file from a GitHub repository's default branch."""
    validate_repository(owner, repo)

    if not isinstance(path, str):
        raise ValueError("Path must be a string")

    if (
        not path
        or path.startswith("/")
        or "\\" in path
        or any(part in ("", ".", "..") for part in path.split("/"))
    ):
        raise ValueError("Invalid repository file path")

    encoded_path = "/".join(quote(part, safe="") for part in path.split("/"))

    data = github_request(f"/repos/{owner}/{repo}/contents/{encoded_path}")

    if not isinstance(data, dict) or data.get("type") != "file":
        raise ValueError("The requested path is not a file")

    if data.get("size", 0) > MAX_GITHUB_FILE_BYTES:
        raise ValueError("File exceeds the 100 KB size limit")

    if data.get("encoding") != "base64":
        raise ValueError(
            f"GitHub did not return Base64 content for '{path}'. "
            f"Encoding: {data.get('encoding')!r}"
        )

    encoded_content = data.get("content")

    if not isinstance(encoded_content, str):
        raise ValueError(f"GitHub returned invalid content for '{path}'")

    try:
        raw_content = base64.b64decode(
            encoded_content,
            validate=False,
        )
        content = raw_content.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError(f"File '{path}' is not valid UTF-8 text") from exc

    try:
        raw_content = base64.b64decode(
            data["content"],
            validate=False,
        )
        content = raw_content.decode("utf-8")
    except (ValueError, UnicodeDecodeError) as exc:
        raise ValueError("File is not valid UTF-8 text") from exc

    if len(raw_content) > MAX_GITHUB_FILE_BYTES:
        raise ValueError("Decoded file exceeds the 100 KB size limit")

    return {
        "repository": f"{owner}/{repo}",
        "path": data["path"],
        "size_bytes": len(raw_content),
        "content": content,
    }


SEARCHABLE_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".json",
    ".md",
    ".yaml",
    ".yml",
    ".toml",
    ".html",
    ".css",
    ".sql",
    ".sh",
}

IGNORED_SEARCH_DIRS = {
    ".git",
    ".venv",
    "node_modules",
    "__pycache__",
    "dist",
    "build",
}

MAX_SEARCH_FILES = 40
MAX_SEARCH_FILE_BYTES = 100_000
MAX_SEARCH_TOTAL_BYTES = 1_000_000
MAX_SEARCH_RESULTS = 50


def search_github_code(
    owner: str,
    repo: str,
    query: str,
) -> dict:
    """Search source files for a literal, case-insensitive keyword."""
    validate_repository(owner, repo)

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query must not be empty")

    query = query.strip()

    if len(query) > 200:
        raise ValueError("Search query must be 200 characters or fewer")

    # Find the repository's default branch.
    repo_info = get_github_repo_info(owner, repo)
    branch = quote(repo_info["default_branch"], safe="")

    # Fetch the repository tree in one API request.
    tree_data = github_request(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")

    tree = tree_data.get("tree", [])
    truncated = tree_data.get("truncated", False)

    # Keep only supported text files and skip generated directories.
    candidates = []

    for item in tree:
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        parts = path.split("/")

        if any(part in IGNORED_SEARCH_DIRS for part in parts):
            continue

        if Path(path).suffix.lower() not in SEARCHABLE_EXTENSIONS:
            continue

        size = item.get("size", 0)

        if size > MAX_SEARCH_FILE_BYTES:
            continue

        candidates.append(item)

    candidates.sort(key=lambda item: item["path"])
    candidates = candidates[:MAX_SEARCH_FILES]

    results = []
    scanned_files = 0
    scanned_bytes = 0

    for item in candidates:
        size = item.get("size", 0)

        # Keep total downloaded source bounded.
        if scanned_bytes + size > MAX_SEARCH_TOTAL_BYTES:
            continue

        blob = github_request(f"/repos/{owner}/{repo}/git/blobs/{item['sha']}")

        if blob.get("encoding") != "base64":
            continue

        try:
            raw = base64.b64decode(blob["content"])
            content = raw.decode("utf-8")
        except (ValueError, UnicodeDecodeError, KeyError):
            # Skip malformed or binary content.
            continue

        scanned_files += 1
        scanned_bytes += len(raw)

        for line_number, line in enumerate(content.splitlines(), start=1):
            if query.casefold() not in line.casefold():
                continue

            results.append(
                {
                    "path": item["path"],
                    "line": line_number,
                    "text": line.strip()[:300],
                }
            )

            if len(results) >= MAX_SEARCH_RESULTS:
                break

        if len(results) >= MAX_SEARCH_RESULTS:
            break

    return {
        "repository": f"{owner}/{repo}",
        "query": query,
        "matches": results,
        "match_count": len(results),
        "files_scanned": scanned_files,
        "bytes_scanned": scanned_bytes,
        "tree_truncated": truncated,
        "file_limit_reached": len(candidates) >= MAX_SEARCH_FILES,
    }


MAX_RAG_FILES = 20
MAX_RAG_TOTAL_BYTES = 500_000
MAX_RAG_RESULTS = 5


def search_repository_context(
    owner: str,
    repo: str,
    query: str,
) -> dict:
    """Retrieve relevant source-code context using hybrid search."""
    validate_repository(owner, repo)

    if not isinstance(query, str) or not query.strip():
        raise ValueError("Search query must not be empty")

    if len(query) > 200:
        raise ValueError("Search query must be 200 characters or fewer")

    # Discover supported source files in the repository.
    repo_info = get_github_repo_info(owner, repo)
    branch = quote(repo_info["default_branch"], safe="")

    tree_data = github_request(f"/repos/{owner}/{repo}/git/trees/{branch}?recursive=1")

    candidates = []

    for item in tree_data.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        parts = path.split("/")

        if any(part in IGNORED_SEARCH_DIRS for part in parts):
            continue

        if Path(path).suffix.lower() not in SEARCHABLE_EXTENSIONS:
            continue

        size = item.get("size", 0)

        if size > MAX_SEARCH_FILE_BYTES:
            continue

        candidates.append(item)

    candidates.sort(key=lambda item: item["path"])

    # Bound the amount of source code fetched and indexed.
    selected_paths = []
    total_bytes = 0

    for item in candidates:
        size = item.get("size", 0)

        if len(selected_paths) >= MAX_RAG_FILES:
            break

        if total_bytes + size > MAX_RAG_TOTAL_BYTES:
            continue

        selected_paths.append(item["path"])
        total_bytes += size
        
    selected_shas = {
        item["path"]: item["sha"]
        for item in candidates
        if item["path"] in selected_paths
    }
    
    if not selected_paths:
        return {
            "repository": f"{owner}/{repo}",
            "query": query,
            "results": [],
            "message": "No supported source files were found.",
        }

    # Import here to avoid a circular import:
    # repository_index imports functions from this module.
    from devpilot.context_builder import deduplicate_chunks
    from devpilot.hybrid_search import hybrid_search
    from devpilot.index_cache import get_repository_index

    chunks = get_repository_index(
        owner=owner,
        repo=repo,
        paths=selected_paths,
        file_shas=selected_shas,
    )

    results = hybrid_search(
        chunks,
        query,
        limit=MAX_RAG_RESULTS,
    )

    results = deduplicate_chunks(results)

    return {
        "repository": f"{owner}/{repo}",
        "query": query,
        "results": [
            {
                "path": chunk["path"],
                "line_numbers": chunk["line_numbers"],
                "text": chunk["text"],
                "hybrid_score": chunk["hybrid_score"],
            }
            for chunk in results
        ],
    }


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_info",
            "description": "Get basic information about DevPilot.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_project_files",
            "description": (
                "List files and directories in the configured project "
                "directory or one of its subdirectories. Does not read "
                "file contents. Use a relative path such as '.' or 'src'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": (
                            "Relative directory path under the configured "
                            "project root. Defaults to '.'"
                        ),
                    },
                },
                "required": [],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_github_repo_info",
            "description": (
                "Get metadata for a GitHub repository, including its "
                "description, default branch, language, and star count."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                },
                "required": ["owner", "repo"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "list_github_files",
            "description": (
                "List files and directories in a GitHub repository. "
                "Accepts an owner, repository name, and optional relative path."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "path": {
                        "type": "string",
                        "description": "Relative directory path; defaults to '.'",
                    },
                },
                "required": ["owner", "repo"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "read_github_file",
            "description": (
                "Read the text contents of a file in a GitHub repository. "
                "Use the repository owner, repository name, and file path."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["owner", "repo", "path"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_github_code",
            "description": (
                "Search a GitHub repository's supported source files for "
                "a literal keyword. Returns matching file paths, line "
                "numbers, and source lines."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "query": {
                        "type": "string",
                        "description": "Literal keyword or identifier to find.",
                    },
                },
                "required": ["owner", "repo", "query"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_repository_context",
            "description": (
                "Search a GitHub repository for source code relevant "
                "to a question using keyword and semantic retrieval. "
                "Use this for questions about implementation details "
                "or how code works. Returns source snippets with "
                "file paths and exact retained line numbers."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "owner": {"type": "string"},
                    "repo": {"type": "string"},
                    "query": {
                        "type": "string",
                        "description": (
                            "A question describing the code or behavior " "to find."
                        ),
                    },
                },
                "required": ["owner", "repo", "query"],
                "additionalProperties": False,
            },
        },
    },
]


TOOL_FUNCTIONS = {
    "get_project_info": get_project_info,
    "list_project_files": list_project_files,
    "get_github_repo_info": get_github_repo_info,
    "list_github_files": list_github_files,
    "read_github_file": read_github_file,
    "search_github_code": search_github_code,
    "search_repository_context": search_repository_context,
}

TOOL_ALLOWED_ARGUMENTS = {
    "get_project_info": set(),
    "list_project_files": {"path"},
    "get_github_repo_info": {"owner", "repo"},
    "list_github_files": {"owner", "repo", "path"},
    "read_github_file": {"owner", "repo", "path"},
    "search_github_code": {"owner", "repo", "query"},
    "search_repository_context": {"owner", "repo", "query"},
}


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Validate a registered tool request and execute it."""
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary")

    allowed_arguments = TOOL_ALLOWED_ARGUMENTS[name]
    unexpected = set(arguments) - allowed_arguments

    if unexpected:
        raise ValueError(f"Unexpected arguments for {name}: {sorted(unexpected)}")

    return TOOL_FUNCTIONS[name](**arguments)
