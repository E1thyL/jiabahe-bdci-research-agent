from __future__ import annotations

import json

import pytest

from research.value_gate import (
    CandidateProblem,
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    FixtureEvidenceCollector,
    GateDecision,
    ResearchValueGate,
)


def _candidate(**overrides) -> CandidateProblem:
    values = dict(
        problem_statement="Can evidence-preserving context compression improve research agents?",
        research_object="multi-agent research workflow",
        hypothesis="Preserving cited evidence improves quality at lower token cost.",
        topic="context_engineering",
        significance_evidence_ids=("paper-significance",),
        closest_prior_work=("paper-prior",),
        novelty_evidence_ids=("paper-prior",),
        gap="Prior work does not measure evidence retention under compression.",
        difference="We evaluate retention and quality jointly.",
        datasets=("research-tasks",),
        baselines=("full_context", "summary_only"),
        metrics=("task_quality", "token_cost"),
        feasibility_evidence_ids=("paper-prior",),
        expected_contribution=("evidence-retention benchmark",),
    )
    values.update(overrides)
    return CandidateProblem(**values)


def _literature() -> tuple[EvidenceItem, ...]:
    return (
        EvidenceItem(
            "paper-significance", "doi:s", "Significance", ("Author",), 2025,
            "Venue", "importance", "limitation", source_hash="hash-s",
        ),
        EvidenceItem(
            "paper-prior", "doi:p", "Closest Prior", ("Author",), 2024,
            "Venue", "closest prior work", "prior_work", source_hash="hash-p",
        ),
    )


def test_go_allows_method_and_experiment_design_before_results() -> None:
    bundle = FixtureEvidenceCollector(EvidenceBundle(_literature())).collect(_candidate())
    result = ResearchValueGate().evaluate(_candidate(), bundle)

    assert result.decision == GateDecision.GO
    assert result.literature["status"] == "verified"
    assert result.experiment["status"] == "pending"
    assert json.loads(result.to_json())["decision"] == "go"


def test_experiment_is_pending_when_no_experiment_evidence_exists() -> None:
    candidate = _candidate()
    result = ResearchValueGate().evaluate(candidate, _literature())

    assert result.experiment["status"] == "pending"
    assert result.decision == GateDecision.GO


@pytest.mark.parametrize(
    ("field", "expected_objection"),
    [
        ("research_object", "research object is missing"),
        ("hypothesis", "research hypothesis is missing"),
        ("closest_prior_work", "closest prior work is missing"),
        ("baselines", "datasets, baselines, and metrics must all be executable"),
        ("metrics", "datasets, baselines, and metrics must all be executable"),
        ("datasets", "datasets, baselines, and metrics must all be executable"),
    ],
)
def test_hard_gates_block_go(field: str, expected_objection: str) -> None:
    empty_value = "" if field in {"research_object", "hypothesis"} else ()
    result = ResearchValueGate().evaluate(
        _candidate(**{field: empty_value}), _literature()
    )

    assert result.decision == GateDecision.REVISE
    assert expected_objection in result.reviewer_objections


def test_novelty_requires_verified_literature_evidence() -> None:
    evidence = (
        EvidenceItem(
            "paper-significance", "doi:s", "Significance", ("Author",), 2025,
            "Venue", "importance", "limitation", source_hash="hash-s",
        ),
    )

    result = ResearchValueGate().evaluate(_candidate(), evidence)

    assert result.novelty.score == 0
    assert result.literature["status"] == "insufficient"
    assert result.decision == GateDecision.REVISE


def test_pending_literature_cannot_support_go() -> None:
    pending = tuple(
        EvidenceItem(
            item.evidence_id,
            item.source_uri,
            item.title,
            item.authors,
            item.year,
            item.venue,
            item.excerpt,
            item.evidence_type,
            verification_status=EvidenceStatus.PENDING,
            source_hash=item.source_hash,
        )
        for item in _literature()
    )

    result = ResearchValueGate().evaluate(_candidate(), pending)

    assert result.novelty.score == 0
    assert result.decision == GateDecision.REVISE


def test_unknown_assessment_evidence_id_cannot_go() -> None:
    result = ResearchValueGate().evaluate(
        _candidate(novelty_evidence_ids=("missing-paper",)), _literature()
    )

    assert result.decision == GateDecision.REVISE
    assert any("missing-paper" in objection for objection in result.reviewer_objections)


def test_duplicate_evidence_ids_are_rejected() -> None:
    items = _literature()
    with pytest.raises(ValueError, match="must be unique"):
        EvidenceBundle(items + (items[0],))


def test_evidence_types_distinguish_dataset_baseline_and_metric() -> None:
    bundle = EvidenceBundle(
        (
            EvidenceItem("dataset-1", "dataset://tasks", "Dataset", (), 2025,
                         "Venue", "task set", "dataset", source_hash="hash-d"),
            EvidenceItem("baseline-1", "paper://baseline", "Baseline", (), 2024,
                         "Venue", "baseline", "baseline", source_hash="hash-b"),
            EvidenceItem("metric-1", "paper://metric", "Metric", (), 2023,
                         "Venue", "metric", "metric", source_hash="hash-m"),
        )
    )

    assert [item.evidence_type for item in bundle.items] == [
        "dataset", "baseline", "metric"
    ]


def test_topic_policies_cover_the_three_research_directions() -> None:
    for topic in ("context_engineering", "memory_engine", "self_evolution"):
        result = ResearchValueGate().evaluate(_candidate(topic=topic), _literature())
        assert result.problem_statement


def test_unknown_topic_is_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported research topic"):
        ResearchValueGate().evaluate(_candidate(topic="unknown"), _literature())


def test_empty_problem_statement_is_no_go() -> None:
    result = ResearchValueGate().evaluate(
        _candidate(problem_statement=""), _literature()
    )

    assert result.decision == GateDecision.NO_GO
    assert "problem statement is missing" in result.reviewer_objections
