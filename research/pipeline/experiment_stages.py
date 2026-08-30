"""Offline boundaries for experiment execution and result analysis."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Iterable
import math

from ..experiment import ExperimentEvidenceRecord
from ..usage import UsageSink, make_phase_usage_record


@dataclass(frozen=True)
class ExperimentExecutionArtifact:
    research_run_id: str
    status: str
    record_ids: tuple[str, ...]
    verified_record_ids: tuple[str, ...]
    artifact_path: str

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_run_id": self.research_run_id,
            "status": self.status,
            "record_ids": list(self.record_ids),
            "verified_record_ids": list(self.verified_record_ids),
            "artifact_path": self.artifact_path,
        }


@dataclass(frozen=True)
class ResultAnalysisArtifact:
    research_run_id: str
    status: str
    experiment_record_ids: tuple[str, ...]
    artifact_path: str
    analyses: dict[str, dict[str, Any]] = None
    status_reason: str = ""

    def to_dict(self) -> dict[str, Any]:
        return {
            "research_run_id": self.research_run_id,
            "status": self.status,
            "experiment_record_ids": list(self.experiment_record_ids),
            "artifact_path": self.artifact_path,
            "claim_map": None,
            "analyses": self.analyses or {},
            "status_reason": self.status_reason,
        }


class ExperimentExecutionStage:
    """Accept precomputed records without pretending to execute an experiment."""

    def run(
        self,
        research_run_id: str,
        records: Iterable[ExperimentEvidenceRecord] = (),
        *,
        usage_sink: UsageSink | None = None,
    ) -> ExperimentExecutionArtifact:
        if not research_run_id.strip():
            raise ValueError("research_run_id must not be empty")
        records = tuple(records)
        if any(record.research_run_id != research_run_id for record in records):
            raise ValueError("experiment records must match research_run_id")
        ids = tuple(record.record_id for record in records)
        if len(ids) != len(set(ids)):
            raise ValueError("experiment record_id values must be unique")
        verified = tuple(record.record_id for record in records if record.is_verified)
        status = "verified" if verified else "pending"
        artifact = ExperimentExecutionArtifact(
            research_run_id, status, ids, verified,
            f"artifacts/{research_run_id}/experiment_execution.json",
        )
        _record_usage(usage_sink, "experiment_execution", research_run_id)
        return artifact


class ResultAnalysisStage:
    """Create a result-analysis boundary; claim mapping remains unimplemented."""

    def run(
        self,
        research_run_id: str,
        execution: ExperimentExecutionArtifact,
        *,
        records: Iterable[ExperimentEvidenceRecord] = (),
        usage_sink: UsageSink | None = None,
    ) -> ResultAnalysisArtifact:
        if not research_run_id.strip():
            raise ValueError("research_run_id must not be empty")
        if execution.research_run_id != research_run_id:
            raise ValueError("execution artifact must match research_run_id")
        records = tuple(records)
        if not records:
            status, reason, analyses = "pending", "analysis input not supplied", {}
        elif not execution.verified_record_ids:
            status, reason, analyses = "inconclusive", "no verified experiment results", {}
        else:
            # Conservative descriptive analysis.  No significance claim is made.
            analyses = {}
            for record in records:
                analyses[record.record_id] = {
                    "status": "supported" if record.metric_values else "inconclusive",
                    "analysis_method": record.analysis_method or "descriptive",
                    "metrics": record.metric_values,
                    "dispersion": record.dispersion,
                    "run_count": record.run_count,
                    "artifact_path": record.artifact_path,
                    "effect_size": None,
                    "confidence_interval": None,
                    "uncertainties": (["single_run_no_sampling_uncertainty"]
                                      if record.run_count == 1 else []),
                    "limitations": (["effect_size_not_computable_without_paired_baseline"]
                                    if record.baseline_id else []),
                }
            status, reason = "ready", "descriptive analysis generated"
        artifact = ResultAnalysisArtifact(
            research_run_id, status, execution.verified_record_ids,
            f"artifacts/{research_run_id}/result_analysis.json", analyses, reason,
        )
        _record_usage(usage_sink, "result_analysis", research_run_id)
        return artifact


def _record_usage(sink: UsageSink | None, phase: str, research_run_id: str) -> None:
    if sink is not None:
        sink.record(make_phase_usage_record(phase=phase, research_run_id=research_run_id))
