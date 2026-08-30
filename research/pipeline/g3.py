"""Drafting entry gate; deliberately independent of model/reviewer services."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DraftingReadiness:
    status: str
    missing: tuple[str, ...] = ()
    @property
    def ready(self): return self.status == "ready"

def check_drafting_readiness(*, value_gate, execution, analysis, claim_map, evidence, usage_records=(), experiment_records=(), citation_registry=None, required_claim_ids=(), required_claim_types=()):
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
    if citation_registry is None:
        missing.append("citation_registry_missing")
        registry_values = set()
    elif isinstance(citation_registry, dict):
        if citation_registry.get("research_run_id") != execution.research_run_id:
            missing.append("citation_registry_run_id")
        registry_values = set(citation_registry.get("citations", ()))
    else:
        registry_values = set(citation_registry)
    errors=claim_map.validate(evidence, experiment_records=experiment_records, citations=registry_values)
    if errors: missing.append("claim_map")
    claim_ids = {claim.claim_id for claim in claim_map.claims}
    claim_types = {claim.claim_type for claim in claim_map.claims}
    if set(required_claim_ids) - claim_ids: missing.append("required_claims")
    if set(required_claim_types) - claim_types: missing.append("required_claim_types")
    if not usage_records: missing.append("usage")
    elif any(getattr(record, "research_run_id", None) != execution.research_run_id for record in usage_records):
        missing.append("usage_run_id")
    elif any(getattr(record, "measurement_status", None) is None for record in usage_records):
        missing.append("usage_measurement_status")
    return DraftingReadiness("ready" if not missing else "blocked", tuple(dict.fromkeys(missing)))
