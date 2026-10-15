import base64
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
            "GitHub denied the request. Check API rate limits "
            "or repository permissions."
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

    if data.get("encoding") != "base64" or not data.get("content"):
        raise ValueError("GitHub did not return Base64 file content")

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
]


TOOL_FUNCTIONS = {
    "get_project_info": get_project_info,
    "list_project_files": list_project_files,
    "get_github_repo_info": get_github_repo_info,
    "list_github_files": list_github_files,
    "read_github_file": read_github_file,
}

TOOL_ALLOWED_ARGUMENTS = {
    "get_project_info": set(),
    "list_project_files": {"path"},
    "get_github_repo_info": {"owner", "repo"},
    "list_github_files": {"owner", "repo", "path"},
    "read_github_file": {"owner", "repo", "path"},
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
