from devpilot.llm import ask_llm_with_tools

result = ask_llm_with_tools(
    "Use the available tool to find the current milestone of DevPilot."
)

print(result)
