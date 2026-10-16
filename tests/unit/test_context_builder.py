
from devpilot.context_builder import deduplicate_chunks


def test_overlapping_chunks():
    chunks = [
        {
            "path": "src/example.py",
            "start_line": 1,
            "end_line": 4,
            "text": "line 1\nline 2\nline 3\nline 4",
            "score": 0.9,
        },
        {
            "path": "src/example.py",
            "start_line": 3,
            "end_line": 6,
            "text": "line 3\nline 4\nline 5\nline 6",
            "score": 0.8,
        },
    ]

    result = deduplicate_chunks(chunks)

    assert len(result) == 2
    assert result[0]["text"] == (
        "line 1\nline 2\nline 3\nline 4"
    )
    assert result[1]["text"] == "line 5\nline 6"
    assert result[1]["score"] == 0.8
    assert result[0]["line_numbers"] == [1, 2, 3, 4]
    assert result[1]["line_numbers"] == [5, 6]

    print("Context deduplication test passed")

def test_fully_duplicate_chunk_is_removed():
    chunks = [
        {
            "path": "src/example.py",
            "start_line": 1,
            "end_line": 2,
            "text": "line 1\nline 2",
        },
        {
            "path": "src/example.py",
            "start_line": 1,
            "end_line": 2,
            "text": "line 1\nline 2",
        },
    ]

    result = deduplicate_chunks(chunks)

    assert len(result) == 1
    assert result[0]["line_numbers"] == [1, 2]

if __name__ == "__main__":
    test_overlapping_chunks()
    test_fully_duplicate_chunk_is_removed()
