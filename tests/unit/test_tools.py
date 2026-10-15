
from devpilot.tools import execute_tool, get_project_info

# Test the Python function directly.
print("Direct result:")
print(get_project_info())

# Test the execution gate.
print("\nTool execution result:")
print(execute_tool("get_project_info", {}))
