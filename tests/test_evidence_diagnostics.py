# Step 18C - Evidence Diagnostics Tests
#
# Role:
#   Verify evidence quality diagnostics before route-aware generation.
#
# Why this exists:
#   Evidence diagnostics will later influence answering, abstention, fallback,
#   and verification. The metrics must be deterministic and explainable.
#
# Input:
#   Synthetic RetrievalResult evidence and RoutePolicy values.
#
# Output:
#   Passing pytest checks for strength, spread, risk, and serialization.

from pytest import approx

from backend.evidence.diagnostics import (
    EvidenceStrength,
    diagnose_evidence,
    evidence_diagnostics_to_dict,
)
from backend.retrieval.models import RetrievalResult
from backend.routing.policy import RouteName, ROUTE_POLICIES


def make_result(
    chunk_id: str,
    document_id: int,
    score: float,
    title: str,
    text: str,
    source_name: str = "FCA",
) -> RetrievalResult:
    return RetrievalResult(
        rank=int(chunk_id),
        score=score,
        retrieval_method="hybrid",
        chunk_id=chunk_id,
        document_id=document_id,
        chunk_index=0,
        title=title,
        source_name=source_name,
        source_url="https://example.com",
        chunk_text=text,
    )


def test_diagnostics_handles_empty_evidence() -> None:
    diagnostics = diagnose_evidence(
        "What is an Authorised Person?",
        [],
        ROUTE_POLICIES[RouteName.SIMPLE],
    )

    assert diagnostics.retrieved_count == 0
    assert diagnostics.evidence_strength == EvidenceStrength.NONE
    assert diagnostics.top_score == 0.0
    assert diagnostics.reasons == ("No evidence was retrieved.",)


def test_simple_route_detects_strong_evidence() -> None:
    evidence = [
        make_result(
            "1",
            10,
            1.0,
            "Authorised Person definition",
            "An Authorised Person is a firm with financial services permission.",
        )
    ]

    diagnostics = diagnose_evidence(
        "What is an Authorised Person?",
        evidence,
        ROUTE_POLICIES[RouteName.SIMPLE],
    )

    assert diagnostics.evidence_strength == EvidenceStrength.STRONG
    assert diagnostics.strong_passage_count == 1
    assert diagnostics.source_document_count == 1


def test_complex_route_rewards_multiple_strong_documents() -> None:
    evidence = [
        make_result(
            "1",
            10,
            0.9,
            "Notification approval requirement",
            "The firm must notify the regulator and seek approval under these conditions.",
        ),
        make_result(
            "2",
            11,
            0.8,
            "Controller change approval",
            "A controller change may require approval and notification before proceeding.",
        ),
        make_result(
            "3",
            12,
            0.7,
            "Regulator notification duty",
            "The regulator expects notification when firm control changes.",
        ),
    ]

    diagnostics = diagnose_evidence(
        "Does the firm need approval and notification when its controller changes?",
        evidence,
        ROUTE_POLICIES[RouteName.COMPLEX],
    )

    assert diagnostics.evidence_strength == EvidenceStrength.STRONG
    assert diagnostics.source_document_count == 3
    assert diagnostics.strong_passage_count >= 3
    assert "approval" in diagnostics.risk_markers
    assert "notify" in diagnostics.risk_markers


def test_diagnostics_counts_duplicate_documents_and_score_margin() -> None:
    evidence = [
        make_result("1", 10, 0.9, "FCA notification", "Notification requirement."),
        make_result("2", 10, 0.7, "FCA notification", "Notification requirement."),
    ]

    diagnostics = diagnose_evidence(
        "What notification requirements apply?",
        evidence,
        ROUTE_POLICIES[RouteName.MEDIUM],
    )

    assert diagnostics.duplicate_document_count == 1
    assert diagnostics.score_margin == approx(0.2)


def test_diagnostics_detects_cross_reference_signal() -> None:
    evidence = [
        make_result(
            "1",
            10,
            0.9,
            "Section X and Section Y",
            "These sections should be read together across multiple documents.",
        )
    ]

    diagnostics = diagnose_evidence(
        "What does Section X require when read together with Section Y?",
        evidence,
        ROUTE_POLICIES[RouteName.COMPLEX],
    )

    assert diagnostics.has_cross_reference_signal is True


def test_evidence_diagnostics_serializes_to_dict() -> None:
    diagnostics = diagnose_evidence(
        "What is an Authorised Person?",
        [
            make_result(
                "1",
                10,
                1.0,
                "Authorised Person definition",
                "An Authorised Person is a firm with permission.",
            )
        ],
        ROUTE_POLICIES[RouteName.SIMPLE],
    )

    payload = evidence_diagnostics_to_dict(diagnostics)

    assert payload["route_name"] == "simple"
    assert payload["retrieved_count"] == 1
    assert payload["evidence_strength"] == "strong"
