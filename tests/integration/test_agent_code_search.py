
from devpilot.agent import run_agent

def test_agent_code_search():
    answer = run_agent(
        "In the GitHub repository tusharkotlapure/test_ai_agent, "
        "find where execute_tool is defined and give me the file path "
        "and line number. Use the GitHub code search tool."
    )

    print(answer)


if __name__ == "__main__":
    test_agent_code_search()
