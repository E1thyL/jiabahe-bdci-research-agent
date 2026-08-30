"""Drafting entry gate; deliberately independent of model/reviewer services."""
from dataclasses import dataclass
@dataclass(frozen=True)
class DraftingReadiness:
    status: str
    missing: tuple[str, ...] = ()
    @property
    def ready(self): return self.status == "ready"

def check_drafting_readiness(*, value_gate, execution, analysis, claim_map, evidence, usage_records=(), experiment_records=(), citation_registry=None, required_claim_ids=(), required_claim_types=(), artifact_store=None):
    missing=[]
    if artifact_store is None: missing.append("artifact_store_missing")
    claim_path = getattr(claim_map, "artifact_path", "")
    if not claim_path: missing.append("claim_map_artifact_reference")
    elif artifact_store is not None and not _valid_artifact(artifact_store, claim_path, execution.research_run_id, "claim_map"): missing.append("claim_map_artifact_invalid")
    decision = getattr(value_gate, "decision", None)
    if decision is None or getattr(decision, "value", decision) == "no_go": missing.append("value_gate")
    if not execution.verified_record_ids: missing.append("verified_experiment")
    if execution.status != "verified": missing.append("complete_experiment_artifact")
    execution_path = getattr(execution, "artifact_path", "")
    if not execution_path: missing.append("experiment_artifact_reference")
    elif execution.research_run_id not in execution_path.replace("\\", "/").split("/"): missing.append("experiment_artifact_scope")
    elif artifact_store is not None and not _valid_artifact(artifact_store, execution_path, execution.research_run_id, "experiment_execution"): missing.append("experiment_artifact_invalid")
    if analysis.status != "ready": missing.append("result_analysis")
    analysis_path = getattr(analysis, "artifact_path", "")
    if not analysis_path: missing.append("analysis_artifact_reference")
    elif execution.research_run_id not in analysis_path.replace("\\", "/").split("/"): missing.append("analysis_artifact_scope")
    elif artifact_store is not None and not _valid_artifact(artifact_store, analysis_path, execution.research_run_id, "result_analysis"): missing.append("analysis_artifact_invalid")
    if execution_records := tuple(record for record in experiment_records if record.is_verified):
        for record in execution_records:
            if not record.metric_artifact_refs:
                missing.append("metric_artifact_refs_missing")
            if set(record.metric_artifact_refs) != set(record.metric_values):
                missing.append("metric_artifact_refs_incomplete")
            for metric, reference in record.metric_artifact_refs.items():
                if not isinstance(reference, str) or "#" not in reference:
                    missing.append("metric_artifact_ref_format")
                    continue
                base, pointer = reference.split("#", 1)
                if not _path_in_run(base, execution.research_run_id) or not _resolve_pointer_format(pointer):
                    missing.append("metric_artifact_ref_format")
                    continue
                item = None if artifact_store is None else artifact_store.resolve(base)
                if item is None or not _valid_artifact(artifact_store, base, execution.research_run_id, "metric"):
                    missing.append(f"metric_artifact_invalid:{metric}")
                    continue
                try:
                    actual = _resolve_pointer(item.content, pointer)
                except (KeyError, IndexError, TypeError, ValueError):
                    missing.append(f"metric_artifact_pointer_missing:{metric}")
                    continue
                expected = record.metric_values.get(metric)
                if not _nonempty(actual) or type(actual) is not type(expected) or actual != expected:
                    missing.append(f"metric_artifact_value_mismatch:{metric}")
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

def _valid_artifact(store, path, run_id, artifact_type):
    item = store.resolve(path)
    allowed = {"metric", "result", "experiment_result", "experiment_execution"} if artifact_type == "metric" else {artifact_type}
    return item is not None and _path_in_run(path, run_id) and item.research_run_id == run_id and item.artifact_type in allowed and bool(item.content)

def _path_in_run(path, run_id):
    from pathlib import PurePosixPath
    p = PurePosixPath(path.replace("\\", "/"))
    return not p.is_absolute() and ".." not in p.parts and run_id in p.parts

def _resolve_pointer_format(pointer):
    return isinstance(pointer, str) and pointer.startswith("/") and pointer != "/" and all(part == "" or "~" not in part.replace("~0", "").replace("~1", "") for part in pointer.split("/"))

def _resolve_pointer(content, pointer):
    value = content
    for token in pointer.split("/")[1:]:
        if "~" in token and any(x not in {"~0", "~1"} for x in _tilde_parts(token)):
            raise ValueError("invalid JSON pointer escape")
        token = token.replace("~1", "/").replace("~0", "~")
        if isinstance(value, dict): value = value[token]
        elif isinstance(value, list): value = value[int(token)]
        else: raise TypeError("pointer target is not traversable")
    return value

def _tilde_parts(token):
    import re
    return re.findall(r"~.", token)

def _nonempty(value):
    return value is not None and value != "" and value != {} and value != []
