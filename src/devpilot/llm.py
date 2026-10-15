
from openai import OpenAI

from devpilot.config import (
    OPENROUTER_API_KEY,
    OPENROUTER_MODEL,
)
from devpilot.tools import TOOL_DEFINITIONS

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
