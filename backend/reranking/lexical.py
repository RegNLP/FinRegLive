# Step 16 - Lexical Reranker
#
# Role:
#   Reorder retrieved chunks using query-term overlap and original rank.
#
# Why this exists:
#   Hybrid retrieval is a first-pass candidate finder. It can still include
#   weak chunks, especially when vector search finds broad semantic matches.
#   This reranker is a small local baseline before adding heavier cross-encoder
#   reranking later.
#
# Input:
#   A user question and candidate RetrievalResult objects.
#
# Output:
#   RetrievalResult objects reordered by reranking score.

import re
from collections import Counter

from backend.retrieval.models import RetrievalResult


TOKEN_PATTERN = re.compile(r"[a-z0-9]+")
STOP_WORDS = {
    "about",
    "after",
    "also",
    "and",
    "are",
    "for",
    "from",
    "has",
    "have",
    "how",
    "into",
    "latest",
    "mention",
    "mentions",
    "new",
    "recent",
    "recently",
    "the",
    "this",
    "that",
    "their",
    "they",
    "what",
    "when",
    "where",
    "which",
    "with",
}


def tokenize(text: str) -> list[str]:
    return [
        token
        for token in TOKEN_PATTERN.findall(text.lower())
        if len(token) > 2 and token not in STOP_WORDS
    ]


def score_candidate(question_tokens: list[str], candidate: RetrievalResult) -> float:
    if not question_tokens:
        return 1.0 / (candidate.rank + 10)

    query_counts = Counter(question_tokens)
    title_counts = Counter(tokenize(candidate.title))
    text_counts = Counter(tokenize(candidate.chunk_text))

    query_total = sum(query_counts.values())
    title_overlap = sum(
        min(count, title_counts[token]) for token, count in query_counts.items()
    )
    text_overlap = sum(
        min(count, text_counts[token]) for token, count in query_counts.items()
    )

    title_score = title_overlap / query_total
    text_score = text_overlap / query_total
    original_rank_score = 1.0 / (candidate.rank + 10)

    return (2.0 * title_score) + text_score + (0.25 * original_rank_score)


def rerank_lexical(
    question: str,
    candidates: list[RetrievalResult],
    top_k: int,
) -> list[RetrievalResult]:
    question_tokens = tokenize(question)

    scored_candidates = [
        (score_candidate(question_tokens, candidate), candidate)
        for candidate in candidates
    ]
    scored_candidates.sort(key=lambda item: item[0], reverse=True)

    reranked_results: list[RetrievalResult] = []
    for rank, (score, candidate) in enumerate(scored_candidates[:top_k], start=1):
        reranked_results.append(
            candidate.model_copy(
                update={
                    "rank": rank,
                    "score": score,
                    "retrieval_method": "hybrid_reranked",
                }
            )
        )

    return reranked_results
