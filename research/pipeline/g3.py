"""Drafting entry gate; deliberately independent of model/reviewer services."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DraftingReadiness:
    status: str
    missing: tuple[str, ...] = ()
    @property
    def ready(self): return self.status == "ready"

def check_drafting_readiness(*, value_gate, execution, analysis, claim_map, evidence, usage_records=()):
    missing=[]
    decision = getattr(value_gate, "decision", None)
    if decision is None or getattr(decision, "value", decision) == "no_go": missing.append("value_gate")
    if not execution.verified_record_ids: missing.append("verified_experiment")
    if execution.status != "verified": missing.append("complete_experiment_artifact")
    if analysis.status != "ready": missing.append("result_analysis")
    errors=claim_map.validate(evidence)
    if errors: missing.append("claim_map")
    if not usage_records: missing.append("usage")
    return DraftingReadiness("ready" if not missing else "blocked", tuple(dict.fromkeys(missing)))
