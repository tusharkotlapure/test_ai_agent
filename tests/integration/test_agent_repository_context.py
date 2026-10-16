
from devpilot.agent import run_agent


def main():
    question = (
        "In the GitHub repository tusharkotlapure/test_ai_agent, "
        "explain where registered tools are executed. "
        "Use search_repository_context to retrieve relevant source code "
        "before answering, and cite the file paths and line numbers."
    )

    answer = run_agent(question)

    print("\nDEVPILOT ANSWER")
    print(answer)


if __name__ == "__main__":
    main()
