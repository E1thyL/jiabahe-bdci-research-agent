from __future__ import annotations

import pytest

from research import ExperimentEvidenceRecord, ExperimentExecutionStatus
from research.pipeline import ExperimentExecutionStage, ResultAnalysisStage
from research.value_gate import EvidenceStatus


def verified_record(run_id="run-1"):
    return ExperimentEvidenceRecord(
        record_id="exp-1", research_run_id=run_id, method_id="method", baseline_id="base",
        dataset_id="data", dataset_source_uri="https://example.org/data", dataset_source_hash="hash",
        config_snapshot={"seed": 1}, seed=1, metric_values={"score": 0.8}, dispersion={"score": 0.1},
        run_count=2, analysis_method="mean", execution_status=ExperimentExecutionStatus.COMPLETED,
        verification_status=EvidenceStatus.VERIFIED, artifact_path=f"artifacts/{run_id}/experiment.json",
        metric_artifact_refs={"score": f"artifacts/{run_id}/experiment.json#/score"},
    )


def test_empty_offline_execution_is_pending_and_analysis_is_pending():
    execution = ExperimentExecutionStage().run("run-1")
    analysis = ResultAnalysisStage().run("run-1", execution)
    assert execution.status == "pending"
    assert analysis.status == "pending"
    assert analysis.to_dict()["claim_map"] is None


def test_verified_records_are_preserved_for_analysis():
    execution = ExperimentExecutionStage().run("run-1", (verified_record(),))
    analysis = ResultAnalysisStage().run("run-1", execution)
    assert execution.status == "verified"
    assert execution.verified_record_ids == ("exp-1",)
    assert analysis.status == "ready"
    assert analysis.experiment_record_ids == ("exp-1",)


def test_cross_run_records_are_rejected():
    with pytest.raises(ValueError, match="match research_run_id"):
        ExperimentExecutionStage().run("run-2", (verified_record("run-1"),))
