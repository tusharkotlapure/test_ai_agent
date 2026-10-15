
import json

from devpilot.llm import client, ask_llm_with_tools
from devpilot.tools import TOOL_DEFINITIONS, execute_tool


MAX_ITERATIONS = 5


def run_agent(question: str) -> str:
    messages = [
        {
            "role": "system",
            "content": (
                "You are DevPilot, an AI assistant for software developers. "
                "Use tools when helpful, and answer the user based on "
                "the available information."
            ),
        },
        {"role": "user", "content": question},
    ]

    for _ in range(MAX_ITERATIONS):
        response = client.chat.completions.create(
            model=__import__(
                "devpilot.config", fromlist=["OPENROUTER_MODEL"]
            ).OPENROUTER_MODEL,
            messages=messages,
            tools=TOOL_DEFINITIONS,
            tool_choice="auto",
        )

        message = response.choices[0].message

        if not message.tool_calls:
            if message.content:
                return message.content
            raise RuntimeError("The model returned an empty response")

        # Preserve the assistant's original tool-call message.
        messages.append(message.model_dump(exclude_none=True))

        for tool_call in message.tool_calls:
            tool_name = tool_call.function.name

            try:
                arguments = json.loads(tool_call.function.arguments)
                result = execute_tool(tool_name, arguments)
                tool_content = json.dumps(result)
            except (ValueError, TypeError, json.JSONDecodeError) as exc:
                tool_content = json.dumps(
                    {"error": str(exc)}
                )

            # Return the execution result to the LLM.
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": tool_content,
                }
            )

    raise RuntimeError(
        f"Agent exceeded the maximum of {MAX_ITERATIONS} iterations"
    )
