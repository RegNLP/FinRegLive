# Step 16 - Reranking Tests
#
# Role:
#   Verify the local reranker improves candidate order deterministically.
#
# Why this exists:
#   Reranking changes which evidence reaches answer generation, so the basic
#   ordering behavior should be protected by tests.
#
# Input:
#   Synthetic RetrievalResult candidates.
#
# Output:
#   Passing pytest checks for reranked order and metadata.

from backend.reranking.lexical import rerank_lexical
from backend.retrieval.models import RetrievalResult


def make_candidate(
    chunk_id: str,
    rank: int,
    title: str,
    text: str,
) -> RetrievalResult:
    return RetrievalResult(
        rank=rank,
        score=1.0 / rank,
        retrieval_method="hybrid",
        chunk_id=chunk_id,
        document_id=rank,
        chunk_index=0,
        title=title,
        source_name="FCA",
        source_url="https://example.com",
        chunk_text=text,
    )


def test_lexical_reranker_promotes_stronger_question_match() -> None:
    weak_candidate = make_candidate(
        chunk_id="weak",
        rank=1,
        title="Unauthorised firm warning",
        text="This firm may be providing financial services without permission.",
    )
    strong_candidate = make_candidate(
        chunk_id="strong",
        rank=2,
        title="Listing rules for closed ended investment funds",
        text="The FCA is consulting on listing rules and investment funds.",
    )

    results = rerank_lexical(
        "What FCA updates mention listing rules for investment funds?",
        [weak_candidate, strong_candidate],
        top_k=2,
    )

    assert [result.chunk_id for result in results] == ["strong", "weak"]
    assert results[0].rank == 1
    assert results[0].retrieval_method == "hybrid_reranked"


def test_lexical_reranker_limits_output_to_top_k() -> None:
    candidates = [
        make_candidate("1", 1, "Listing rules", "Investment funds update."),
        make_candidate("2", 2, "Consumer duty", "Consumer duty update."),
    ]

    results = rerank_lexical("listing rules", candidates, top_k=1)

    assert len(results) == 1
    assert results[0].chunk_id == "1"
