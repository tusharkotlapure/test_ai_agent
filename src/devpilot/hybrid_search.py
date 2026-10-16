
from devpilot.code_index import search_index
from devpilot.semantic_search import semantic_search


def hybrid_search(
    chunks: list[dict],
    query: str,
    limit: int = 5,
    candidate_limit: int = 20,
    rrf_k: int = 60,
) -> list[dict]:
    """Combine keyword and semantic rankings using RRF."""
    if not query.strip():
        raise ValueError("Query must not be empty")

    if limit <= 0 or candidate_limit <= 0 or rrf_k <= 0:
        raise ValueError("Limits and rrf_k must be positive")

    keyword_results = search_index(
        chunks, query, limit=candidate_limit
    )
    semantic_results = semantic_search(
        chunks, query, limit=candidate_limit
    )

    fused = {}

    def chunk_key(result: dict) -> tuple:
        return (
            result["path"],
            result["start_line"],
            result["end_line"],
        )

    for ranking_name, results in (
        ("keyword", keyword_results),
        ("semantic", semantic_results),
    ):
        for rank, result in enumerate(results, start=1):
            key = chunk_key(result)

            if key not in fused:
                fused[key] = {
                    **result,
                    "hybrid_score": 0.0,
                    "keyword_rank": None,
                    "semantic_rank": None,
                    "keyword_score": None,
                    "semantic_score": None,
                }

            fused[key][f"{ranking_name}_rank"] = rank
            fused[key][f"{ranking_name}_score"] = result["score"]
            fused[key]["hybrid_score"] += 1 / (rrf_k + rank)

    ranked = sorted(
        fused.values(),
        key=lambda item: (
            -item["hybrid_score"],
            item["path"],
            item["start_line"],
        ),
    )

    return ranked[:limit]
