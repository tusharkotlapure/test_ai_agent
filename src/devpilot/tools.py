
from pathlib import Path
from typing import Any

from devpilot.config import DEVPILOT_PROJECT_ROOT


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

        entries.append({
            "name": entry.name,
            "type": "directory" if entry.is_dir() else "file",
        })

        if len(entries) >= MAX_ENTRIES:
            break

    return {
        "path": str(requested_path.relative_to(root)) or ".",
        "entries": entries,
        "count": len(entries),
        "truncated": len(entries) == MAX_ENTRIES,
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
]


TOOL_FUNCTIONS = {
    "get_project_info": get_project_info,
    "list_project_files": list_project_files,
}

TOOL_ALLOWED_ARGUMENTS = {
    "get_project_info": set(),
    "list_project_files": {"path"},
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
        raise ValueError(
            f"Unexpected arguments for {name}: {sorted(unexpected)}"
        )

    return TOOL_FUNCTIONS[name](**arguments)
