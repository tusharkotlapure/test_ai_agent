
from typing import Any


def get_project_info() -> dict[str, str]:
    """Return basic information about the DevPilot project."""
    return {
        "name": "DevPilot",
        "purpose": "AI assistant for software developers",
        "language": "Python",
        "current_milestone": "Agent loop and tool calling",
    }


# Describes the tool to the LLM.
TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "get_project_info",
            "description": (
                "Get the name, purpose, language, and current milestone "
                "of the DevPilot project."
            ),
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        },
    }
]


# Maps the tool name to the actual Python function.
TOOL_FUNCTIONS = {
    "get_project_info": get_project_info,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> Any:
    """Validate and execute a registered tool."""
    if name not in TOOL_FUNCTIONS:
        raise ValueError(f"Unknown tool: {name}")

    if not isinstance(arguments, dict):
        raise ValueError("Tool arguments must be a dictionary")

    if arguments:
        raise ValueError(f"{name} does not accept arguments")

    return TOOL_FUNCTIONS[name]()
