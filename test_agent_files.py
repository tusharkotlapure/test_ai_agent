from devpilot.agent import run_agent

answer = run_agent(
    "Inspect the project files and tell me which Python modules "
    "are inside the src/devpilot directory. Use the available tools."
)

print(answer)