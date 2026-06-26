# Step 17A - Basic Local Evaluation Runner
#
# Role:
#   Run saved evaluation questions through local RAG answer generation.
#
# Why this exists:
#   Manual testing is useful, but it is not repeatable. This runner creates a
#   baseline evaluation file that compares normal hybrid retrieval with
#   hybrid-plus-reranking without using another LLM judge.
#
# Input:
#   evaluation/questions.jsonl
#
# Output:
#   JSONL result files under evaluation/results/.

import argparse
import json
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from time import perf_counter
from typing import Any

from backend.generation.answer import answer_question
from backend.generation.models import GroundedAnswer


DEFAULT_QUESTIONS_PATH = Path("evaluation/questions.jsonl")
DEFAULT_RESULTS_DIR = Path("evaluation/results")
ABSTENTION_MARKERS = (
    "insufficient",
    "no evidence",
    "not enough evidence",
    "cannot answer",
    "can't answer",
    "does not contain",
    "do not contain",
)

AnswerFunction = Callable[..., GroundedAnswer]


@dataclass(frozen=True)
class EvaluationQuestion:
    id: str
    category: str
    question: str


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as file:
        for line_number, line in enumerate(file, start=1):
            stripped_line = line.strip()
            if not stripped_line:
                continue
            try:
                records.append(json.loads(stripped_line))
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on line {line_number}: {path}") from exc
    return records


def load_questions(path: Path) -> list[EvaluationQuestion]:
    questions: list[EvaluationQuestion] = []
    for record in read_jsonl(path):
        try:
            questions.append(
                EvaluationQuestion(
                    id=str(record["id"]),
                    category=str(record["category"]),
                    question=str(record["question"]),
                )
            )
        except KeyError as exc:
            raise ValueError(f"Question record is missing required field: {record}") from exc
    return questions


def source_ids(answer: GroundedAnswer) -> list[str]:
    return [source.chunk_id for source in answer.sources]


def answer_abstained(answer: GroundedAnswer) -> bool:
    answer_text = answer.answer.strip().lower()
    if answer_text.startswith("the retrieved evidence is insufficient"):
        return True
    if answer_text.startswith("i cannot answer") or answer_text.startswith("i can't answer"):
        return True

    limitation_text = " ".join(answer.limitations[:2]).lower()
    return any(marker in limitation_text for marker in ABSTENTION_MARKERS)


def answer_metrics(answer: GroundedAnswer, latency_ms: int) -> dict[str, Any]:
    ids = source_ids(answer)
    unique_ids = set(ids)

    return {
        "latency_ms": latency_ms,
        "has_answer": bool(answer.answer.strip()),
        "answer_char_count": len(answer.answer),
        "answer_word_count": len(answer.answer.split()),
        "has_sources": bool(answer.sources),
        "source_count": len(ids),
        "unique_source_count": len(unique_ids),
        "duplicate_source_count": len(ids) - len(unique_ids),
        "limitation_count": len(answer.limitations),
        "abstained": answer_abstained(answer),
    }


def serialize_answer(answer: GroundedAnswer, latency_ms: int) -> dict[str, Any]:
    return {
        "answer": answer.answer,
        "sources": [source.model_dump() for source in answer.sources],
        "limitations": answer.limitations,
        "metrics": answer_metrics(answer, latency_ms),
    }


def run_answer(
    question: str,
    top_k: int,
    use_reranking: bool,
    answer_function: AnswerFunction = answer_question,
) -> dict[str, Any]:
    started_at = perf_counter()
    answer = answer_function(
        question,
        top_k=top_k,
        use_reranking=use_reranking,
    )
    latency_ms = int((perf_counter() - started_at) * 1000)
    return serialize_answer(answer, latency_ms)


def compare_runs(hybrid_run: dict[str, Any], reranked_run: dict[str, Any]) -> dict[str, Any]:
    hybrid_ids = {source["chunk_id"] for source in hybrid_run["sources"]}
    reranked_ids = {source["chunk_id"] for source in reranked_run["sources"]}

    return {
        "same_sources": hybrid_ids == reranked_ids,
        "source_overlap_count": len(hybrid_ids & reranked_ids),
        "hybrid_only_source_count": len(hybrid_ids - reranked_ids),
        "reranked_only_source_count": len(reranked_ids - hybrid_ids),
        "answer_changed": hybrid_run["answer"] != reranked_run["answer"],
    }


def evaluate_question(
    question: EvaluationQuestion,
    top_k: int,
    answer_function: AnswerFunction = answer_question,
) -> dict[str, Any]:
    hybrid_run = run_answer(
        question.question,
        top_k=top_k,
        use_reranking=False,
        answer_function=answer_function,
    )
    reranked_run = run_answer(
        question.question,
        top_k=top_k,
        use_reranking=True,
        answer_function=answer_function,
    )

    return {
        "question_id": question.id,
        "category": question.category,
        "question": question.question,
        "top_k": top_k,
        "runs": {
            "hybrid": hybrid_run,
            "hybrid_reranked": reranked_run,
        },
        "comparison": compare_runs(hybrid_run, reranked_run),
    }


def summarize_results(results: list[dict[str, Any]]) -> dict[str, Any]:
    if not results:
        return {
            "question_count": 0,
            "hybrid_with_sources": 0,
            "reranked_with_sources": 0,
            "changed_source_sets": 0,
            "changed_answers": 0,
        }

    return {
        "question_count": len(results),
        "hybrid_with_sources": sum(
            result["runs"]["hybrid"]["metrics"]["has_sources"] for result in results
        ),
        "reranked_with_sources": sum(
            result["runs"]["hybrid_reranked"]["metrics"]["has_sources"]
            for result in results
        ),
        "changed_source_sets": sum(
            not result["comparison"]["same_sources"] for result in results
        ),
        "changed_answers": sum(
            result["comparison"]["answer_changed"] for result in results
        ),
    }


def write_jsonl(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as file:
        for record in records:
            file.write(json.dumps(record, ensure_ascii=False) + "\n")


def default_output_path(results_dir: Path) -> Path:
    timestamp = datetime.now(UTC).strftime("%Y%m%d_%H%M%S")
    return results_dir / f"basic_eval_{timestamp}.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run basic local RAG evaluation.")
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--results-dir", type=Path, default=DEFAULT_RESULTS_DIR)
    parser.add_argument("--output", type=Path, default=None)
    parser.add_argument("--top-k", type=int, default=5)
    parser.add_argument("--limit", type=int, default=None)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    questions = load_questions(args.questions)
    if args.limit is not None:
        questions = questions[: args.limit]

    results = [
        evaluate_question(question, top_k=args.top_k)
        for question in questions
    ]
    output_path = args.output or default_output_path(args.results_dir)
    write_jsonl(output_path, results)

    summary = summarize_results(results)
    print(json.dumps({"output": str(output_path), "summary": summary}, indent=2))


if __name__ == "__main__":
    main()
