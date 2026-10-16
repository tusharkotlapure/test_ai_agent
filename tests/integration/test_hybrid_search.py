
from devpilot.hybrid_search import hybrid_search
from devpilot.repository_index import build_repository_index


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

    results = hybrid_search(chunks, query, limit=5)

    print("\nHYBRID SEARCH")
    for result in results:
        print(
            f"\n{result['path']}:{result['start_line']}-"
            f"{result['end_line']}"
        )
        print(f"Hybrid score: {result['hybrid_score']:.4f}")
        print(f"Keyword rank: {result['keyword_rank']}")
        print(f"Semantic rank: {result['semantic_rank']}")
        print(result["text"][:200])


if __name__ == "__main__":
    main()
