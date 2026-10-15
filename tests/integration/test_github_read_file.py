
from devpilot.tools import execute_tool

result = execute_tool(
    "read_github_file",
    {
        "owner": "tusharkotlapure",
        "repo": "test_ai_agent",
        "path": "src/devpilot/agent.py",
    },
)

print("Repository:", result["repository"])
print("File:", result["path"])
print("Size:", result["size_bytes"], "bytes")
print("\nSource code:\n")
print(result["content"])
