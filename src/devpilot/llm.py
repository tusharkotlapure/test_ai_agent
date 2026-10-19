from openai import OpenAI

from devpilot.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)
from devpilot.tools import TOOL_DEFINITIONS
from devpilot.context_builder import deduplicate_chunks
from devpilot.citation_validator import validate_citations

client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)


def ask_llm(question: str) -> str:
    """Ask the LLM a normal question."""
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are DevPilot, an AI assistant "
                    "that helps software developers."
                ),
            },
            {"role": "user", "content": question},
        ],
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("The model returned an empty response")

    return answer


def ask_llm_with_tools(question: str) -> dict:
    """Ask the LLM to use an available tool."""
    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are DevPilot, an AI assistant that helps "
                    "software developers. Use tools when relevant."
                ),
            },
            {"role": "user", "content": question},
        ],
        tools=TOOL_DEFINITIONS,
        tool_choice="auto",
    )

    message = response.choices[0].message

    if message.tool_calls:
        tool_calls = []

        for call in message.tool_calls:
            tool_calls.append(
                {
                    "id": call.id,
                    "type": "function",
                    "function": {
                        "name": call.function.name,
                        "arguments": call.function.arguments,
                    },
                }
            )

        return {
            "type": "tool_call",
            "message": {
                "role": "assistant",
                "content": message.content,
                "tool_calls": tool_calls,
            },
        }

    if message.content:
        return {
            "type": "final_answer",
            "content": message.content,
        }

    raise RuntimeError("The model returned neither a tool call nor an answer")


def ask_llm_with_context(question: str, context_chunks: list[dict]) -> str:
    """Answer a question using retrieved source-code context."""
    if not question.strip():
        raise ValueError("Question must not be empty")

    if not context_chunks:
        return "I couldn't find relevant source code to answer " "this question."

    context_chunks = deduplicate_chunks(context_chunks)

    context_parts = []

    context_parts = []

    for chunk in context_chunks:
        if "line_numbers" in chunk:
            numbered_source = "\n".join(
                f"{line_number}: {line}"
                for line_number, line in zip(
                    chunk["line_numbers"],
                    chunk["text"].splitlines(),
                )
            )
            line_reference = ", ".join(str(number) for number in chunk["line_numbers"])
        else:
            numbered_source = "\n".join(
                f"{chunk['start_line'] + offset}: {line}"
                for offset, line in enumerate(chunk["text"].splitlines())
            )
            line_reference = f"{chunk['start_line']}-{chunk['end_line']}"

        context_parts.append(
            f"File: {chunk['path']}\n"
            f"Source lines: {line_reference}\n"
            f"Source code:\n{numbered_source}"
        )

    context = "\n\n---\n\n".join(context_parts)

    response = client.chat.completions.create(
        model=OPENROUTER_MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "Only cite file paths and line numbers explicitly present in "
                    "the retrieved context. Do not invent line numbers or infer "
                    "source code that was not provided."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Question:\n{question}\n\n"
                    f"Retrieved source-code context:\n{context}"
                ),
            },
        ],
    )

    answer = response.choices[0].message.content

    if not answer:
        raise RuntimeError("The model returned an empty response")

    validation = validate_citations(answer, context_chunks)

    if not validation["has_citations"]:
        return answer + (
            "\n\nNote: This answer contains no citations in the "
            "supported file-path:line-number format."
        )

    invalid_citations = [
        citation
        for citation in validation["citations"]
        if not citation["valid"]
    ]

    if invalid_citations:
        invalid_references = ", ".join(
            f"{citation['path']}:{citation['start_line']}"
            if citation["start_line"] == citation["end_line"]
            else (
                f"{citation['path']}:"
                f"{citation['start_line']}-{citation['end_line']}"
            )
            for citation in invalid_citations
        )

        return answer + (
            "\n\nWarning: The following citations could not be verified "
            f"against the retrieved context: {invalid_references}"
        )

    return answer
