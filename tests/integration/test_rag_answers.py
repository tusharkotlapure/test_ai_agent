
from devpilot.hybrid_search import hybrid_search
from devpilot.llm import ask_llm_with_context
from devpilot.repository_index import build_repository_index
from devpilot.context_builder import deduplicate_chunks

def main():
    chunks = build_repository_index(
        owner="tusharkotlapure",
        repo="test_ai_agent",
        paths=[
            "src/devpilot/agent.py",
            "src/devpilot/tools.py",
            "src/devpilot/config.py",
        ],
    )

    question = "Where does the application execute a registered tool?"

    retrieved_chunks = hybrid_search(
        chunks,
        question,
        limit=5,
    )
    
    context_chunks = deduplicate_chunks(retrieved_chunks)

    print("\nCONTEXT AFTER DEDUPLICATION")
    for chunk in context_chunks:
        print(
            f"{chunk['path']}:"
            f"{chunk['start_line']}-{chunk['end_line']}"
        )
        print(chunk["text"][:150])

    print("\nRETRIEVED CONTEXT")
    for chunk in retrieved_chunks:
        print(
            f"{chunk['path']}:"
            f"{chunk['start_line']}-{chunk['end_line']}"
        )

    answer = ask_llm_with_context(
        question=question,
        context_chunks=context_chunks,
    )

    print("\nRAG ANSWER")
    print(answer)


if __name__ == "__main__":
    main()
