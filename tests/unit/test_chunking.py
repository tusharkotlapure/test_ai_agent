
from devpilot.chunking import chunk_text

def test_chunk_text_preserves_line_ranges():
    text = "\n".join(f"line {i}" for i in range(1, 191))

    chunks = chunk_text(text, chunk_size=80, overlap=10)

    assert len(chunks) == 3
    assert chunks[0]["start_line"] == 1
    assert chunks[0]["end_line"] == 80
    assert chunks[1]["start_line"] == 71
    assert chunks[1]["end_line"] == 150
    assert chunks[2]["start_line"] == 141
    assert chunks[2]["end_line"] == 190


def test_chunk_text_handles_empty_input():
    assert chunk_text("") == []


if __name__ == "__main__":
    test_chunk_text_preserves_line_ranges()
    test_chunk_text_handles_empty_input()
    print("Chunking tests passed")
