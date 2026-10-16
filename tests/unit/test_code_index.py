
from devpilot.code_index import index_source_file, search_index


def test_index_and_search():
    source = """\
def execute_tool(name, arguments):
    if name not in TOOL_FUNCTIONS:
        raise ValueError("Unknown tool")

    return TOOL_FUNCTIONS[name](**arguments)
"""

    chunks = index_source_file(
        "src/devpilot/tools.py",
        source,
        chunk_size=3,
        overlap=1,
    )

    results = search_index(chunks, "TOOL_FUNCTIONS")

    assert results
    assert results[0]["path"] == "src/devpilot/tools.py"
    assert results[0]["score"] > 0


def test_search_returns_no_results_for_unmatched_query():
    chunks = index_source_file(
        "example.py",
        "def add(a, b):\n    return a + b",
        chunk_size=10,
        overlap=2,
    )

    assert search_index(chunks, "nonexistent_identifier") == []


if __name__ == "__main__":
    test_index_and_search()
    test_search_returns_no_results_for_unmatched_query()
    print("Code index tests passed")
