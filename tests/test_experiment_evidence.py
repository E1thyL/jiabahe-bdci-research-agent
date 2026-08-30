from __future__ import annotations

from dataclasses import replace

import pytest

from research import ExperimentEvidenceRecord, ExperimentExecutionStatus
from research.value_gate import (
    CandidateProblem,
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    ResearchValueGate,
    ScientificSupportLevel,
)


def _record(**overrides) -> ExperimentEvidenceRecord:
    values = dict(
        record_id="experiment-001",
        research_run_id="run-001",
        method_id="proposed-method",
        baseline_id="baseline-001",
        dataset_id="dataset-001",
        dataset_source_uri="https://example.test/dataset",
        dataset_source_hash="dataset-hash",
        config_snapshot={"temperature": 0},
        seed=7,
        metric_values={"quality": 0.8},
        dispersion={"quality": 0.1},
        run_count=3,
        analysis_method="mean and standard deviation",
        execution_status=ExperimentExecutionStatus.COMPLETED,
        verification_status=EvidenceStatus.VERIFIED,
        artifact_path="artifacts/run-001/experiment.json",
        metric_artifact_refs={
            "quality": "artifacts/run-001/experiment.json#/metrics/quality"
        },
    )
    values.update(overrides)
    return ExperimentEvidenceRecord(**values)


def test_complete_record_is_verified_and_json_round_trips() -> None:
    record = _record()

    assert record.is_verified
    assert record.support_level is ScientificSupportLevel.EXPERIMENT
    assert ExperimentEvidenceRecord.from_json(record.to_json()) == record


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("artifact_path", "", "artifact_path"),
        ("seed", None, "seed"),
        ("baseline_id", "", "baseline_id"),
        ("metric_artifact_refs", {}, "metric_artifact_refs"),
    ],
)
def test_verified_record_rejects_missing_required_provenance(
    field: str, value: object, message: str
) -> None:
    with pytest.raises(ValueError, match=message):
        _record(**{field: value})


def test_verified_record_rejects_untraceable_metric() -> None:
    with pytest.raises(ValueError, match="traceable"):
        _record(metric_artifact_refs={"quality": "other.json#/quality"})


def test_verified_record_rejects_empty_config_snapshot() -> None:
    with pytest.raises(ValueError, match="config_snapshot or config_hash"):
        _record(config_snapshot={}, config_hash="")


def test_failed_execution_cannot_be_verified() -> None:
    with pytest.raises(ValueError, match="completed execution"):
        _record(execution_status=ExperimentExecutionStatus.FAILED)


def test_pending_record_can_be_incomplete() -> None:
    record = ExperimentEvidenceRecord("experiment-pending", "run-pending")

    assert record.verification_status is EvidenceStatus.PENDING
    assert not record.is_verified


def test_gate_uses_verified_parallel_experiment_records() -> None:
    prior = EvidenceItem(
        "prior", "https://example.test/prior", "Prior", (), 2025, "Venue",
        "excerpt", "prior_work", source_hash="prior-hash",
    )
    dataset = EvidenceItem(
        "dataset", "https://example.test/dataset", "Dataset", (), 2025, "Venue",
        "dataset", "dataset", source_hash="dataset-hash",
    )
    candidate = CandidateProblem(
        problem_statement="test problem",
        research_object="research agents",
        hypothesis="the method improves quality",
        topic="context_engineering",
        significance_evidence_ids=("prior",),
        closest_prior_work=("prior",),
        novelty_evidence_ids=("prior",),
        gap="a gap",
        difference="a difference",
        datasets=("dataset-001",),
        baselines=("full_context", "summary_only"),
        metrics=("task_quality", "token_cost"),
        feasibility_evidence_ids=("prior",),
    )

    result = ResearchValueGate().evaluate(
        candidate,
        EvidenceBundle((prior, dataset)),
        experiment_records=(_record(),),
    )

    assert result.experiment == {
        "status": EvidenceStatus.VERIFIED,
        "evidence_ids": ("experiment-001",),
    }


def test_duplicate_experiment_record_ids_are_rejected() -> None:
    from research.value_gate.evidence import EvidenceIndex

    with pytest.raises(ValueError, match="record_id values must be unique"):
        EvidenceIndex(experiment_records=(_record(), replace(_record(), method_id="other")))
