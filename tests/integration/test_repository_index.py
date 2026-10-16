
from devpilot.repository_index import build_repository_index
from devpilot.code_index import search_index


def test_repository_index():
    chunks = build_repository_index(
        owner="tusharkotlapure",
        repo="test_ai_agent",
        paths=[
            "src/devpilot/agent.py",
            "src/devpilot/tools.py",
        ],
    )

    print("Indexed chunks:", len(chunks))

    results = search_index(chunks, "execute_tool")

    for result in results:
        print(
            f"{result['path']}:{result['start_line']}-"
            f"{result['end_line']} "
            f"(score={result['score']})"
        )

    assert chunks
    assert results


if __name__ == "__main__":
    test_repository_index()
