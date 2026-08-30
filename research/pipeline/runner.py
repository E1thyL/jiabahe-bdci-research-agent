"""Minimal end-to-end research pipeline orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol

from ..literature.router import LiteratureRouter
from ..usage import UsageSink, make_phase_usage_record
from ..value_gate.evidence import AdapterEvidenceCollector
from ..value_gate.gate import ResearchValueGate
from ..value_gate.schema import CandidateProblem, EvidenceBundle, GateDecision
from ..experiment import ExperimentEvidenceRecord
from ..claim_map import ClaimMap
from .experiment_stages import ExperimentExecutionStage, ResultAnalysisStage
from .g3 import check_drafting_readiness


class ModelClient(Protocol):
    model: str
    def generate(self, prompt: str, **kwargs: Any) -> str: ...


@dataclass(frozen=True)
class PipelineResult:
    research_run_id: str
    artifacts: dict[str, dict[str, Any]]
    evidence: EvidenceBundle
    decision: Any
    status: str


class ResearchPipelineRunner:
    """Run deterministic stage boundaries while preserving the Value Gate."""

    def __init__(self, *, literature_router: LiteratureRouter, gate: ResearchValueGate | None = None,
                 model_client: ModelClient | None = None, usage_sink: UsageSink | None = None) -> None:
        self.router, self.gate, self.client, self.usage = literature_router, gate or ResearchValueGate(), model_client, usage_sink

    def run(self, candidate: CandidateProblem, *, research_run_id: str,
            topic_config: dict[str, Any] | None = None,
            experiment_records: tuple[ExperimentEvidenceRecord, ...] = (),
            claim_map: ClaimMap | None = None) -> PipelineResult:
        artifacts: dict[str, dict[str, Any]] = {}
        self._stage(artifacts, "ideation", research_run_id, candidate.problem_statement)
        # The runner owns one record per pipeline stage. Direct router callers
        # may still request their own literature measurement explicitly.
        search = self.router.search(candidate, topic_config)
        evidence = search.to_evidence_bundle()
        artifacts["literature"] = self._artifact(research_run_id, {"status": search.status.value, "query": search.query, "evidence_ids": sorted(evidence.ids())})
        if self.usage is not None:
            self.usage.record(make_phase_usage_record(phase="literature", research_run_id=research_run_id,
                model=getattr(self.client, "model", "")))
        decision = self.gate.evaluate(candidate, evidence, usage_sink=self.usage, research_run_id=research_run_id,
            experiment_records=experiment_records)
        artifacts["value_gate"] = self._artifact(research_run_id, decision.to_dict())
        if decision.decision != GateDecision.GO:
            return PipelineResult(research_run_id, artifacts, evidence, decision, "revise")
        for phase in ("method_design", "experiment_design"):
            self._stage(artifacts, phase, research_run_id, f"placeholder for {phase}")
        execution = ExperimentExecutionStage().run(research_run_id, experiment_records, usage_sink=self.usage)
        analysis = ResultAnalysisStage().run(research_run_id, execution, records=experiment_records, usage_sink=self.usage)
        artifacts["experiment_execution"] = self._artifact(research_run_id, execution.to_dict())
        artifacts["result_analysis"] = self._artifact(research_run_id, analysis.to_dict())
        if claim_map is None:
            claim_map = ClaimMap()
        readiness = check_drafting_readiness(value_gate=decision, execution=execution,
            analysis=analysis, claim_map=claim_map, evidence=evidence, usage_records=())
        if experiment_records or claim_map is not None:
            artifacts["drafting_g3"] = self._artifact(research_run_id, {"status": readiness.status, "missing": list(readiness.missing)})
        return PipelineResult(research_run_id, artifacts, evidence, decision,
            "ready" if readiness.ready else "drafting_blocked")

    def _stage(self, artifacts: dict[str, dict[str, Any]], phase: str, run_id: str, prompt: str) -> None:
        content = f"placeholder for {phase}"
        if self.client is not None:
            content = self.client.generate(prompt, _usage_phase=phase)
        artifacts[phase] = self._artifact(run_id, {"content": content})
        if self.usage is not None:
            self.usage.record(make_phase_usage_record(phase=phase, research_run_id=run_id,
                model=getattr(self.client, "model", "")))

    @staticmethod
    def _artifact(run_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        return {"research_run_id": run_id, **payload}
