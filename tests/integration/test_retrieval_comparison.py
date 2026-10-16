
from devpilot.code_index import search_index
from devpilot.repository_index import build_repository_index
from devpilot.semantic_search import semantic_search


def main():
    chunks = build_repository_index(
        owner="tusharkotlapure",
        repo="test_ai_agent",
        paths=[
            "src/devpilot/agent.py",
            "src/devpilot/tools.py",
            "src/devpilot/config.py",
        ],
    )

    query = "Where does the application execute a registered tool?"

    keyword_results = search_index(chunks, query, limit=3)
    semantic_results = semantic_search(chunks, query, limit=3)

    print("\nKEYWORD SEARCH")
    for result in keyword_results:
        print(
            f"{result['path']}:{result['start_line']}-"
            f"{result['end_line']} score={result['score']}"
        )

    print("\nSEMANTIC SEARCH")
    for result in semantic_results:
        print(
            f"{result['path']}:{result['start_line']}-"
            f"{result['end_line']} score={result['score']:.4f}"
        )


if __name__ == "__main__":
    main()
