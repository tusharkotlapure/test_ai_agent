
from devpilot.tools import execute_tool

repo_info = execute_tool(
    "get_github_repo_info",
    {"owner": "tusharkotlapure", "repo": "test_ai_agent"},
)

print("Repository metadata:")
print(repo_info)

root_files = execute_tool(
    "list_github_files",
    {"owner": "tusharkotlapure", "repo": "test_ai_agent"},
)

print("\nRepository files:")
print(root_files)
