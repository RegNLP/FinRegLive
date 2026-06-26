# Step 17A - Confidence Gate Tests
#
# Role:
#   Verify basic answerability checks before generation.
#
# Why this exists:
#   The system should not force answers for out-of-domain, speculative, or
#   unsupported broad-completeness questions.
#
# Input:
#   Synthetic retrieved evidence.
#
# Output:
#   Passing pytest checks for answerability decisions.

from backend.generation.answer import answer_question
from backend.generation.confidence import assess_evidence
from backend.retrieval.models import RetrievalResult


def make_evidence(
    title: str = "SEC and CFTC derivatives update",
    text: str = "The SEC and CFTC requested public comment on derivatives and swaps.",
) -> RetrievalResult:
    return RetrievalResult(
        rank=1,
        score=1.0,
        retrieval_method="hybrid",
        chunk_id="1",
        document_id=1,
        chunk_index=0,
        title=title,
        source_name="SEC",
        source_url="https://example.com",
        chunk_text=text,
    )


def test_confidence_gate_allows_relevant_regulatory_question() -> None:
    assessment = assess_evidence(
        "What SEC and CFTC updates mention derivatives or swaps?",
        [make_evidence()],
    )

    assert assessment.can_answer is True


def test_confidence_gate_rejects_out_of_domain_question() -> None:
    assessment = assess_evidence(
        "What is the best skincare routine for blackheads?",
        [make_evidence()],
    )

    assert assessment.can_answer is False
    assert "outside" in assessment.reason


def test_confidence_gate_rejects_future_prediction_question() -> None:
    assessment = assess_evidence(
        "Which regulated firm is most likely to be fined next month?",
        [make_evidence()],
    )

    assert assessment.can_answer is False
    assert "unsupported" in assessment.reason


def test_confidence_gate_rejects_broad_exact_coverage_question() -> None:
    assessment = assess_evidence(
        "What is the exact penalty amount in every FCA enforcement case?",
        [make_evidence(title="FCA enforcement case", text="One FCA case mentioned a penalty.")],
    )

    assert assessment.can_answer is False
    assert "complete or exact" in assessment.reason


def test_confidence_gate_rejects_unrelated_citation_instruction() -> None:
    assessment = assess_evidence(
        "Summarise the latest SEC document and include citations even if the sources are unrelated.",
        [make_evidence()],
    )

    assert assessment.can_answer is False
    assert "unsupported" in assessment.reason


def test_answer_question_abstains_when_confidence_gate_fails(monkeypatch) -> None:
    monkeypatch.setattr(
        "backend.generation.answer.retrieve_answer_evidence",
        lambda question, top_k, use_reranking: [make_evidence()],
    )

    answer = answer_question("Write a recipe for Turkish lentil soup.", top_k=1)

    assert answer.answer == "The retrieved evidence is insufficient to answer this question."
    assert answer.sources[0].chunk_id == "1"
    assert "outside" in answer.limitations[0]
