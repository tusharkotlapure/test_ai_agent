
from devpilot.citation_validator import validate_citations


CONTEXT = [
    {
        "path": "src/devpilot/tools.py",
        "line_numbers": [10, 11, 12, 13, 14],
        "text": "line 10\nline 11\nline 12\nline 13\nline 14",
    }
]


def test_valid_citation():
    result = validate_citations(
        "The function is defined in src/devpilot/tools.py:10-12.",
        CONTEXT,
    )

    assert result["is_valid"] is True
    assert result["has_citations"] is True
    assert len(result["citations"]) == 1


def test_invalid_line_number():
    result = validate_citations(
        "See src/devpilot/tools.py:99.",
        CONTEXT,
    )

    assert result["is_valid"] is False
    assert result["citations"][0]["valid"] is False


def test_unknown_file():
    result = validate_citations(
        "See src/devpilot/unknown.py:10.",
        CONTEXT,
    )

    assert result["is_valid"] is False


def test_missing_citations():
    result = validate_citations(
        "The function processes repository files.",
        CONTEXT,
    )

    assert result["has_citations"] is False
    assert result["is_valid"] is True


def test_invalid_line_range():
    result = validate_citations(
        "See src/devpilot/tools.py:12-99.",
        CONTEXT,
    )

    assert result["is_valid"] is False


def test_natural_language_citation():
    result = validate_citations(
        "See src/devpilot/tools.py, lines 10-12.",
        CONTEXT,
    )

    assert result["has_citations"] is True
    assert result["is_valid"] is True
   

def test_bold_natural_language_citation():
    answer = (
        "The function is in **`src/devpilot/tools.py`** "
        "(lines **10-12**)."
    )

    context = [
        {
            "path": "src/devpilot/tools.py",
            "line_numbers": [10, 11, 12],
            "text": "line 10\nline 11\nline 12",
        }
    ]

    result = validate_citations(answer, context)

    assert result["has_citations"] is True
    assert result["is_valid"] is True
     
if __name__ == "__main__":
    test_valid_citation()
    test_invalid_line_number()
    test_unknown_file()
    test_missing_citations()
    test_invalid_line_range()
    test_natural_language_citation()
    test_bold_natural_language_citation()
    print("Citation validator tests passed")
