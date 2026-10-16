from devpilot.tools import execute_tool

def test_search_github_code():
    result = execute_tool(
        "search_github_code",
        {
            "owner": "tusharkotlapure",
            "repo": "test_ai_agent",
            "query": "execute_tool",
        },
    )

    print("Files scanned:", result["files_scanned"])
    print("Matches:", result["match_count"])

    for match in result["matches"]:
        print(f"{match['path']}:{match['line']}: " f"{match['text']}")

    assert result["query"] == "execute_tool"
    assert result["match_count"] > 0


if __name__ == "__main__":
    test_search_github_code()
