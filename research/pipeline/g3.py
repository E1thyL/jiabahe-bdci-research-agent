"""Drafting entry gate; deliberately independent of model/reviewer services."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DraftingReadiness:
    status: str
    missing: tuple[str, ...] = ()
    @property
    def ready(self): return self.status == "ready"

def check_drafting_readiness(*, value_gate, execution, analysis, claim_map, evidence, usage_records=(), experiment_records=()):
    missing=[]
    decision = getattr(value_gate, "decision", None)
    if decision is None or getattr(decision, "value", decision) == "no_go": missing.append("value_gate")
    if not execution.verified_record_ids: missing.append("verified_experiment")
    if execution.status != "verified": missing.append("complete_experiment_artifact")
    execution_path = getattr(execution, "artifact_path", "")
    if not execution_path: missing.append("experiment_artifact_reference")
    elif execution.research_run_id not in execution_path.replace("\\", "/").split("/"): missing.append("experiment_artifact_scope")
    if analysis.status != "ready": missing.append("result_analysis")
    analysis_path = getattr(analysis, "artifact_path", "")
    if not analysis_path: missing.append("analysis_artifact_reference")
    elif execution.research_run_id not in analysis_path.replace("\\", "/").split("/"): missing.append("analysis_artifact_scope")
    errors=claim_map.validate(evidence, experiment_records=experiment_records)
    if errors: missing.append("claim_map")
    if not usage_records: missing.append("usage")
    elif any(getattr(record, "research_run_id", None) != execution.research_run_id for record in usage_records):
        missing.append("usage_run_id")
    elif any(getattr(record, "measurement_status", None) is None for record in usage_records):
        missing.append("usage_measurement_status")
    return DraftingReadiness("ready" if not missing else "blocked", tuple(dict.fromkeys(missing)))
