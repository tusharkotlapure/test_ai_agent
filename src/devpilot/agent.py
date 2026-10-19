
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
                "Use tools when helpful and base answers on available evidence. "
                "For questions asking how code works, where functionality is "
                "implemented, or how components interact in a GitHub repository, "
                "prefer search_repository_context first. It performs keyword and "
                "semantic retrieval and returns relevant source snippets with "
                "line numbers. Use read_github_file when the user asks to inspect "
                "a specific known file, and use other tools for their specific "
                "purposes. Cite file paths and line numbers when source context "
                "supports your answer."
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
            print(f"[DevPilot] Calling tool: {tool_name}")
            
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
