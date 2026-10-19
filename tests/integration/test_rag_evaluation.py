
from urllib.parse import quote

from devpilot.code_index import search_index
from devpilot.hybrid_search import hybrid_search
from devpilot.repository_index import build_repository_index
from devpilot.semantic_search import semantic_search
from devpilot.tools import (
    github_request,
    get_github_repo_info,
    IGNORED_SEARCH_DIRS,
    SEARCHABLE_EXTENSIONS,
    MAX_SEARCH_FILE_BYTES,
    MAX_RAG_FILES,
    MAX_RAG_TOTAL_BYTES,
)


OWNER = "tusharkotlapure"
REPO = "test_ai_agent"
TOP_K = 5

EVALUATION_CASES = [
    {
        "question": "Where does the application execute a registered tool?",
        "expected_files": ["src/devpilot/tools.py"],
    },
    {
        "question": "Where does the agent invoke tools?",
        "expected_files": ["src/devpilot/agent.py"],
    },
    {
        "question": "Where is the LLM client configured?",
        "expected_files": ["src/devpilot/llm.py"],
    },
    {
        "question": "How are source files split into chunks?",
        "expected_files": ["src/devpilot/chunking.py"],
    },
    {
        "question": "How are text embeddings generated?",
        "expected_files": ["src/devpilot/embeddings.py"],
    },
]


def reciprocal_rank(results: list[dict], expected_files: list[str]) -> float:
    """Return the reciprocal rank of the first expected file."""
    for rank, result in enumerate(results, start=1):
        if result["path"] in expected_files:
            return 1.0 / rank

    return 0.0

def select_repository_paths() -> list[str]:
    """Select a bounded set of searchable files from the repository."""
    repo_info = get_github_repo_info(OWNER, REPO)
    branch = quote(repo_info["default_branch"], safe="")

    tree_data = github_request(
        f"/repos/{OWNER}/{REPO}/git/trees/{branch}?recursive=1"
    )

    candidates = []

    for item in tree_data.get("tree", []):
        if item.get("type") != "blob":
            continue

        path = item.get("path", "")
        parts = path.split("/")

        if any(part in IGNORED_SEARCH_DIRS for part in parts):
            continue

        if path.rsplit(".", 1)[-1].lower() not in {
            ext.lstrip(".").lower()
            for ext in SEARCHABLE_EXTENSIONS
        }:
            continue

        size = item.get("size", 0)

        if size > MAX_SEARCH_FILE_BYTES:
            continue

        candidates.append(item)

    candidates.sort(key=lambda item: item["path"])

    selected_paths = []
    total_bytes = 0

    for item in candidates:
        size = item.get("size", 0)

        if len(selected_paths) >= MAX_RAG_FILES:
            break

        if total_bytes + size > MAX_RAG_TOTAL_BYTES:
            continue

        selected_paths.append(item["path"])
        total_bytes += size

    return selected_paths


def main():
    paths = select_repository_paths()

    if not paths:
        raise RuntimeError("No searchable repository files were selected.")

    print(f"Indexing {len(paths)} files for evaluation...")
    chunks = build_repository_index(OWNER, REPO, paths)

    methods = {
        "Keyword": lambda query: search_index(
            chunks, query, limit=TOP_K
        ),
        "Semantic": lambda query: semantic_search(
            chunks, query, limit=TOP_K
        ),
        "Hybrid": lambda query: hybrid_search(
            chunks, query, limit=TOP_K
        ),
    }

    hits = {name: 0 for name in methods}
    misses = {name: [] for name in methods}
    reciprocal_rank_totals = {name: 0.0 for name in methods}

    for case in EVALUATION_CASES:
        print(f"\nQuestion: {case['question']}")

        for method_name, search in methods.items():
            results = search(case["question"])
            retrieved_files = {item["path"] for item in results}

            matched = bool(
                retrieved_files.intersection(case["expected_files"])
            )
            
            rr = reciprocal_rank(results, case["expected_files"])
            reciprocal_rank_totals[method_name] += rr

            if matched:
                hits[method_name] += 1
            else:
                misses[method_name].append(case["question"])

            print(
                f"  {method_name}: "
                f"{'HIT' if matched else 'MISS'} "
                f"| {sorted(retrieved_files)}"
            )

    print(f"\n{'=' * 45}")
    print(f"RETRIEVAL RESULTS (Hit Rate@{TOP_K})")
    print(f"{'=' * 45}")
    
    for method_name in methods:
        rate = hits[method_name] / len(EVALUATION_CASES) * 100
        print(
            f"{method_name:10} "
            f"{hits[method_name]}/{len(EVALUATION_CASES)} "
            f"({rate:.1f}%)"
        )

        if misses[method_name]:
            print(f"  Misses: {misses[method_name]}")

    print(f"\n{'=' * 45}")
    print("MEAN RECIPROCAL RANK (MRR)")
    print(f"{'=' * 45}")

    for method_name in methods:
        mrr = reciprocal_rank_totals[method_name] / len(EVALUATION_CASES)
        print(f"{method_name:10} {mrr:.3f}")

if __name__ == "__main__":
    main()
