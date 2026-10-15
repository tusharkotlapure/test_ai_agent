import json

from devpilot.llm import ask_llm_with_tools
from devpilot.tools import execute_tool

question = "Use the available tool to find the current milestone of DevPilot."

# Step 1: Ask the LLM to choose a tool.
llm_result = ask_llm_with_tools(question)
print("LLM tool request:", llm_result)

# Step 2: Execute the requested Python function.
if llm_result["type"] == "tool_call":
    tool_name = llm_result["name"]
    arguments = json.loads(llm_result["arguments"])

    tool_result = execute_tool(tool_name, arguments)

    print("\nExecuted tool:", tool_name)
    print("Tool result:", tool_result)
else:
    print("LLM answered directly:", llm_result["content"])
