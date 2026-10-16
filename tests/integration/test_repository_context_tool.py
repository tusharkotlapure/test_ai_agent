
from devpilot.tools import execute_tool


def main():
    result = execute_tool(
        "search_repository_context",
        {
            "owner": "tusharkotlapure",
            "repo": "test_ai_agent",
            "query": (
                "Where does the application execute a registered tool?"
            ),
        },
    )

    print(f"Repository: {result['repository']}")
    print(f"Query: {result['query']}")

    for item in result["results"]:
        print(f"\n{item['path']}")
        print(f"Lines: {item['line_numbers']}")
        print(f"Hybrid score: {item['hybrid_score']:.4f}")
        print(item["text"][:300])


if __name__ == "__main__":
    main()
