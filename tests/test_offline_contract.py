from research import ExperimentExecutor
from research.claim_map import ClaimLink, ClaimMap
from research.pipeline.g3 import check_drafting_readiness
from research.value_gate import EvidenceBundle, EvidenceItem, EvidenceStatus, ScientificSupportLevel
from types import SimpleNamespace
from research import ArtifactStore
from research.pipeline.experiment_stages import ExperimentExecutionStage, ResultAnalysisStage
from research.value_gate.schema import GateDecision

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

def test_g3_fails_closed_without_citation_registry():
    result = check_drafting_readiness(
        value_gate=SimpleNamespace(decision="go"),
        execution=SimpleNamespace(verified_record_ids=(), status="pending", research_run_id="r", artifact_path="artifacts/r/exp.json"),
        analysis=SimpleNamespace(status="pending", artifact_path="artifacts/r/analysis.json"),
        claim_map=ClaimMap(), evidence=EvidenceBundle(), usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),))
    assert "citation_registry_missing" in result.missing

def test_g3_accepts_complete_artifact_store():
    from test_experiment_stages import verified_record
    store = ArtifactStore()
    record = verified_record("r")
    store.register(path="artifacts/r/exp.json", research_run_id="r", artifact_type="experiment_execution", content={"score": 0.8})
    record = record.__class__(**{**record.to_dict(), "artifact_path": "artifacts/r/exp.json", "metric_artifact_refs": {"score": "artifacts/r/exp.json#/score"}})
    store.register(path="artifacts/r/analysis.json", research_run_id="r", artifact_type="result_analysis", content={"ok": 1})
    claim = ClaimMap((ClaimLink("c1", "limitation", "limit", ("e1",), ("cite-1",), ScientificSupportLevel.FULL_TEXT),), "artifacts/r/claim_map.json")
    store.register(path=claim.artifact_path, research_run_id="r", artifact_type="claim_map", content=claim.to_dict())
    result = check_drafting_readiness(value_gate=SimpleNamespace(decision="go"),
        execution=SimpleNamespace(verified_record_ids=(record.record_id,), status="verified", research_run_id="r", artifact_path="artifacts/r/exp.json"),
        analysis=SimpleNamespace(status="ready", artifact_path="artifacts/r/analysis.json"), claim_map=claim,
        evidence=EvidenceBundle((item(),)), experiment_records=(record,), citation_registry={"research_run_id":"r", "citations":["cite-1"]},
        usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),), artifact_store=store)
    assert result.status == "ready"

def test_g3_requires_metric_artifact_ref():
    from test_experiment_stages import verified_record
    record = verified_record("r")
    execution = ExperimentExecutionStage().run("r", (record,))
    analysis = ResultAnalysisStage().run("r", execution, records=(record,))
    store = ArtifactStore()
    store.register(path=execution.artifact_path, research_run_id="r", artifact_type="experiment_execution", content={"ok":1})
    store.register(path=analysis.artifact_path, research_run_id="r", artifact_type="result_analysis", content={"ok":1})
    claim = ClaimMap((ClaimLink("c", "limitation", "x", ("e1",), ("cite",)),), "artifacts/r/claim.json")
    store.register(path=claim.artifact_path, research_run_id="r", artifact_type="claim_map", content={"ok":1})
    result = check_drafting_readiness(value_gate=SimpleNamespace(decision="go"), execution=execution,
        analysis=analysis, claim_map=claim, evidence=EvidenceBundle((item(),)), experiment_records=(record,),
        citation_registry={"research_run_id":"r", "citations":["cite"]}, usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),), artifact_store=store)
    assert any("metric_artifact" in x for x in result.missing)


def _g3_metric_case(content, ref="artifacts/r/metric.json#/score", metric=0.8, *, path="artifacts/r/metric.json", artifact_type="metric"):
    from test_experiment_stages import verified_record
    record = verified_record("r")
    record = record.__class__(**{**record.to_dict(), "metric_values": {"score": metric}, "artifact_path": path,
                                "metric_artifact_refs": {"score": ref}})
    execution = SimpleNamespace(verified_record_ids=(record.record_id,), status="verified", research_run_id="r",
                                artifact_path="artifacts/r/execution.json")
    analysis = SimpleNamespace(status="ready", artifact_path="artifacts/r/analysis.json")
    claim = ClaimMap((ClaimLink("c", "limitation", "x", ("e1",), ("cite",)),), "artifacts/r/claim.json")
    store = ArtifactStore()
    store.register(path=execution.artifact_path, research_run_id="r", artifact_type="experiment_execution", content={"ok": 1})
    store.register(path=analysis.artifact_path, research_run_id="r", artifact_type="result_analysis", content={"ok": 1})
    store.register(path=claim.artifact_path, research_run_id="r", artifact_type="claim_map", content=claim.to_dict())
    store.register(path=path, research_run_id="r", artifact_type=artifact_type, content=content)
    result = check_drafting_readiness(value_gate=SimpleNamespace(decision="go"), execution=execution, analysis=analysis,
        claim_map=claim, evidence=EvidenceBundle((item(),)), experiment_records=(record,),
        citation_registry={"research_run_id": "r", "citations": ["cite"]},
        usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),), artifact_store=store)
    return result


def test_g3_metric_pointer_nested_and_escaped_fields():
    assert _g3_metric_case({"nested": {"score": 0.8}}, "artifacts/r/metric.json#/nested/score").ready
    assert _g3_metric_case({"a/b": 0.8}, "artifacts/r/metric.json#/a~1b").ready
    assert _g3_metric_case({"a~b": 0.8}, "artifacts/r/metric.json#/a~0b").ready


def test_g3_metric_pointer_missing_empty_and_invalid_are_blocked():
    for content, ref in [({"other": 1}, "artifacts/r/metric.json#/score"), ({"score": None}, "artifacts/r/metric.json#/score"),
                         ({"score": 0.8}, "artifacts/r/metric.json#score"), ({"score": 0.8}, "artifacts/r/metric.json#/bad~2")]:
        assert not _g3_metric_case(content, ref).ready


def test_g3_metric_value_and_type_mismatch_are_blocked():
    assert not _g3_metric_case({"score": 0.7}).ready
    assert not _g3_metric_case({"score": 1}, metric=1.0).ready


def test_g3_metric_path_scope_and_type_are_blocked():
    assert not _g3_metric_case({"score": 0.8}, artifact_type="claim_map").ready


def test_g3_verified_record_without_metric_refs_is_blocked():
    record = SimpleNamespace(is_verified=True, record_id="exp-1", metric_values={"score": 0.8}, metric_artifact_refs={})
    execution = SimpleNamespace(verified_record_ids=("exp-1",), status="verified", research_run_id="r", artifact_path="artifacts/r/execution.json")
    analysis = SimpleNamespace(status="ready", artifact_path="artifacts/r/analysis.json")
    claim = ClaimMap((ClaimLink("c", "limitation", "x", ("e1",), ("cite",)),), "artifacts/r/claim.json")
    store = ArtifactStore()
    for path, kind in ((execution.artifact_path, "experiment_execution"), (analysis.artifact_path, "result_analysis"), (claim.artifact_path, "claim_map")):
        store.register(path=path, research_run_id="r", artifact_type=kind, content={"ok": 1})
    result = check_drafting_readiness(value_gate=SimpleNamespace(decision="go"), execution=execution, analysis=analysis,
        claim_map=claim, evidence=EvidenceBundle((item(),)), experiment_records=(record,),
        citation_registry={"research_run_id": "r", "citations": ["cite"]},
        usage_records=(SimpleNamespace(research_run_id="r", measurement_status="pending"),), artifact_store=store)
    assert not result.ready
    assert "metric_artifact_refs_missing" in result.missing
