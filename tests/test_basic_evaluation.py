# Step 17A - Basic Evaluation Tests
#
# Role:
#   Verify local evaluation helpers without calling real retrieval services.
#
# Why this exists:
#   The evaluation runner should be reliable because it becomes the baseline
#   for comparing future retrieval and generation changes.
#
# Input:
#   Temporary question files and mocked answer functions.
#
# Output:
#   Passing pytest checks for evaluation records and metrics.

from pathlib import Path

from backend.generation.models import AnswerSource, GroundedAnswer
from evaluation.run_basic import (
    EvaluationQuestion,
    compare_runs,
    evaluate_question,
    load_questions,
    summarize_results,
    write_jsonl,
)


def make_answer(question: str, use_reranking: bool) -> GroundedAnswer:
    chunk_id = "reranked" if use_reranking else "hybrid"
    return GroundedAnswer(
        question=question,
        answer=f"Answer from {chunk_id}",
        sources=[
            AnswerSource(
                chunk_id=chunk_id,
                title="Sample",
                source_name="SEC",
                source_url="https://example.com",
            )
        ],
        limitations=["This answer is generated only from retrieved evidence."],
    )


def fake_answer_function(
    question: str,
    top_k: int,
    use_reranking: bool,
) -> GroundedAnswer:
    assert top_k == 2
    return make_answer(question, use_reranking=use_reranking)


def test_load_questions_reads_jsonl(tmp_path: Path) -> None:
    questions_path = tmp_path / "questions.jsonl"
    questions_path.write_text(
        '{"id":"q1","category":"sample","question":"What changed?"}\n',
        encoding="utf-8",
    )

    questions = load_questions(questions_path)

    assert questions == [
        EvaluationQuestion(
            id="q1",
            category="sample",
            question="What changed?",
        )
    ]


def test_evaluate_question_compares_hybrid_and_reranked() -> None:
    result = evaluate_question(
        EvaluationQuestion(
            id="q1",
            category="sample",
            question="What changed?",
        ),
        top_k=2,
        answer_function=fake_answer_function,
    )

    assert result["question_id"] == "q1"
    assert result["runs"]["hybrid"]["sources"][0]["chunk_id"] == "hybrid"
    assert result["runs"]["hybrid_reranked"]["sources"][0]["chunk_id"] == "reranked"
    assert result["comparison"]["same_sources"] is False
    assert result["comparison"]["answer_changed"] is True


def test_compare_runs_counts_source_overlap() -> None:
    hybrid_run = {
        "answer": "A",
        "sources": [{"chunk_id": "1"}, {"chunk_id": "2"}],
    }
    reranked_run = {
        "answer": "B",
        "sources": [{"chunk_id": "2"}, {"chunk_id": "3"}],
    }

    comparison = compare_runs(hybrid_run, reranked_run)

    assert comparison["source_overlap_count"] == 1
    assert comparison["hybrid_only_source_count"] == 1
    assert comparison["reranked_only_source_count"] == 1


def test_summarize_results_counts_basic_metrics() -> None:
    result = evaluate_question(
        EvaluationQuestion(
            id="q1",
            category="sample",
            question="What changed?",
        ),
        top_k=2,
        answer_function=fake_answer_function,
    )

    summary = summarize_results([result])

    assert summary["question_count"] == 1
    assert summary["hybrid_with_sources"] == 1
    assert summary["reranked_with_sources"] == 1
    assert summary["changed_source_sets"] == 1


def test_write_jsonl_creates_result_file(tmp_path: Path) -> None:
    output_path = tmp_path / "results" / "basic_eval.jsonl"

    write_jsonl(output_path, [{"question_id": "q1"}])

    assert output_path.read_text(encoding="utf-8") == '{"question_id": "q1"}\n'
