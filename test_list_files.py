
from devpilot.config import DEVPILOT_PROJECT_ROOT
from devpilot.tools import execute_tool, list_project_files

print("Configured root:", DEVPILOT_PROJECT_ROOT)

print("\nProject root:")
print(execute_tool("list_project_files", {}))

print("\nSource directory:")
print(execute_tool("list_project_files", {"path": "src"}))

print("\nAttempt path traversal:")
try:
    execute_tool("list_project_files", {"path": "../../"})
except ValueError as exc:
    print("Blocked:", exc)
