from research import ExperimentExecutor
from research.claim_map import ClaimLink, ClaimMap
from research.pipeline.g3 import check_drafting_readiness
from research.value_gate import EvidenceBundle, EvidenceItem, EvidenceStatus, ScientificSupportLevel
from types import SimpleNamespace

def item(level=ScientificSupportLevel.FULL_TEXT):
    return EvidenceItem("e1", "https://example.org/p", "Paper", ("A",), 2024, "V", "excerpt", "prior_work", EvidenceStatus.VERIFIED, "hash", level)

def test_executor_is_reproducible_and_offline():
    ex = ExperimentExecutor()
    a = ex.run(experiment_id="x", research_run_id="r", method="m", baseline="b", dataset_provenance="d", seed=7, fixture={"a": 1})
    b = ex.run(experiment_id="x", research_run_id="r", method="m", baseline="b", dataset_provenance="d", seed=7, fixture={"a": 1})
    assert a.metric_values == b.metric_values
    assert a.dataset_source_uri == "offline://fixture"
    assert not a.is_verified

def test_failed_fixture_is_not_verified():
    record = ExperimentExecutor().run(experiment_id="x", research_run_id="r", method="m", baseline="b", dataset_provenance="d", seed=1, fixture=lambda: 1 / 0)
    assert record.execution_status.value == "failed"
    assert not record.is_verified

def test_claim_map_rejects_missing_and_weak_support():
    claim = ClaimLink("c1", "technical_difference", "A difference", ("e1",), ("cite-1",), ScientificSupportLevel.FULL_TEXT)
    assert ClaimMap((claim,)).validate(EvidenceBundle((item(ScientificSupportLevel.ABSTRACT),)))

def test_claim_map_json_round_trip():
    value = ClaimMap((ClaimLink("c1", "limitation", "A limit", ("e1",), ("cite-1",)),)).to_json()
    assert ClaimMap.from_json(value).to_dict()["claims"][0]["claim_id"] == "c1"

def test_claim_map_rejects_unknown_duplicate_and_missing_citation():
    claims = (ClaimLink("c1", "empirical", "x", ("missing",), ()),
              ClaimLink("c1", "limitation", "y", ("e1",), ("cite",)))
    errors = ClaimMap(claims).validate(EvidenceBundle((item(),)))
    assert any("unknown evidence" in error for error in errors)
    assert any("duplicate claim" in error for error in errors)
    assert any("missing citation" in error for error in errors)

def test_g3_blocks_without_usage_and_claims():
    class Gate: decision = "go"
    class Execution: verified_record_ids = ("x",); status = "verified"
    class Analysis: status = "ready"
    result = check_drafting_readiness(value_gate=Gate(), execution=Execution(), analysis=Analysis(), claim_map=ClaimMap(), evidence=EvidenceBundle(), usage_records=())
    assert result.status == "blocked"

def test_g3_rejects_cross_run_artifacts():
    result = check_drafting_readiness(
        value_gate=SimpleNamespace(decision="go"),
        execution=SimpleNamespace(verified_record_ids=("x",), status="verified", research_run_id="r", artifact_path="artifacts/other/exp.json"),
        analysis=SimpleNamespace(status="ready", artifact_path="artifacts/r/analysis.json"),
        claim_map=ClaimMap(), evidence=EvidenceBundle(), usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),))
    assert result.status == "blocked"
