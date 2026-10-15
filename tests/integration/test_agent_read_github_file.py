
from devpilot.agent import run_agent

answer = run_agent(
    "Read src/devpilot/agent.py from the GitHub repository "
    "tusharkotlapure/test_ai_agent and explain how the agent loop works. "
    "Use the GitHub tools to inspect the actual source code."
)

print(answer)
