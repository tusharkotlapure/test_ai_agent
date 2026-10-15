
from devpilot.agent import run_agent

answer = run_agent(
    "Inspect the GitHub repository tusharkotlapure/test_ai_agent. "
    "Tell me its default branch and list the files in its root directory. "
    "Use the available GitHub tools to verify your answer."
)

print(answer)
