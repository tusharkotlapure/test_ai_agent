
from devpilot.semantic_search import semantic_search


def test_semantic_search():
    chunks = [
        {
            "path": "agent.py",
            "start_line": 1,
            "end_line": 3,
            "text": (
                "The agent validates tool arguments and invokes "
                "the registered Python function to execute a tool call."
            ),
        },
        {
            "path": "config.py",
            "start_line": 1,
            "end_line": 3,
            "text": (
                "The application loads environment variables, "
                "configures API credentials, and initializes the "
                "language model client."
            ),
        },
    ]

    results = semantic_search(
        chunks,
        "Where does the application execute a tool by calling its registered Python function?",
        limit=2,
    )

    for result in results:
        print(
            f"{result['path']}: "
            f"score={result['score']:.4f}"
        )

    assert len(results) == 2
    assert all(
        isinstance(result["score"], float)
        for result in results
    )


if __name__ == "__main__":
    test_semantic_search()
    print("Semantic search test passed")
