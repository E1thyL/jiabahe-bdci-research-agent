"""Provenance-bearing experiment result records."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
import json
import hashlib
import math
from pathlib import PurePath
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .value_gate.schema import EvidenceStatus


class ExperimentExecutionStatus(StrEnum):
    PENDING = "pending"
    COMPLETED = "completed"
    FAILED = "failed"

class ExperimentExecutor:
    """Deterministic offline fixture executor; never calls a model or network."""
    def run(self, *, experiment_id: str, research_run_id: str, method: str,
            baseline: str, dataset_provenance: str, seed: int, config: dict[str, Any] | None = None,
            fixture: Any = None) -> "ExperimentEvidenceRecord":
        try:
            fixture_value = fixture() if callable(fixture) else fixture
        except Exception:
            return ExperimentEvidenceRecord(record_id=experiment_id, research_run_id=research_run_id,
                method_id=method, baseline_id=baseline, dataset_id=dataset_provenance,
                execution_status=ExperimentExecutionStatus.FAILED, verification_status="pending")
        payload = json.dumps([experiment_id, method, baseline, dataset_provenance, seed, config or {}, fixture_value], sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode()).hexdigest()
        value = int(digest[:8], 16) / 0xFFFFFFFF
        path = f"artifacts/{research_run_id}/{experiment_id}.json"
        return ExperimentEvidenceRecord(record_id=experiment_id, research_run_id=research_run_id,
            method_id=method, baseline_id=baseline, dataset_id=dataset_provenance,
            dataset_source_uri="offline://fixture", dataset_source_hash=hashlib.sha256(str(fixture_value).encode()).hexdigest(),
            config_snapshot=config or {}, seed=seed, metric_values={"fixture_score": value},
            dispersion={"fixture_score": 0.0}, run_count=1, analysis_method="deterministic_fixture_mean",
            execution_status=ExperimentExecutionStatus.COMPLETED, verification_status="pending",
            artifact_path=path, metric_artifact_refs={"fixture_score": f"{path}#/fixture_score"})


@dataclass(frozen=True)
class ExperimentEvidenceRecord:
    """A single method/baseline result with auditable provenance.

    The record validates structural evidence only. It does not execute an
    experiment or independently recompute metrics from the artifact.
    """

    record_id: str
    research_run_id: str
    method_id: str = ""
    baseline_id: str = ""
    dataset_id: str = ""
    dataset_source_uri: str = ""
    dataset_source_hash: str = ""
    config_snapshot: dict[str, Any] | None = None
    config_hash: str = ""
    seed: int | None = None
    metric_values: dict[str, float] = field(default_factory=dict)
    dispersion: dict[str, float] = field(default_factory=dict)
    run_count: int | None = None
    analysis_method: str = ""
    execution_status: ExperimentExecutionStatus | str = ExperimentExecutionStatus.PENDING
    verification_status: "EvidenceStatus | str" = "pending"
    artifact_path: str = ""
    metric_artifact_refs: dict[str, str] = field(default_factory=dict)
    execution_mode: str = "offline_fixture"

    def __post_init__(self) -> None:
        from .value_gate.schema import EvidenceStatus, ScientificSupportLevel

        if not self.record_id.strip():
            raise ValueError("record_id must not be empty")
        if not self.research_run_id.strip():
            raise ValueError("research_run_id must not be empty")
        if self.execution_mode not in {"offline_fixture", "simulated", "real"}:
            raise ValueError("unsupported execution_mode")

        try:
            execution_status = ExperimentExecutionStatus(self.execution_status)
        except ValueError as exc:
            raise ValueError(
                f"unsupported execution_status: {self.execution_status}"
            ) from exc
        try:
            verification_status = EvidenceStatus(self.verification_status)
        except ValueError as exc:
            raise ValueError(
                f"unsupported verification_status: {self.verification_status}"
            ) from exc
        object.__setattr__(self, "execution_status", execution_status)
        object.__setattr__(self, "verification_status", verification_status)

        if self.config_snapshot is not None and not isinstance(self.config_snapshot, dict):
            raise ValueError("config_snapshot must be a dictionary or None")
        if self.seed is not None and (
            isinstance(self.seed, bool) or not isinstance(self.seed, int)
        ):
            raise ValueError("seed must be an integer or None")
        if self.run_count is not None:
            if isinstance(self.run_count, bool) or not isinstance(self.run_count, int):
                raise ValueError("run_count must be an integer or None")
            if self.run_count < 1:
                raise ValueError("run_count must be positive")

        _validate_measurements(self.metric_values, "metric_values")
        _validate_measurements(self.dispersion, "dispersion", nonnegative=True)
        if any(not isinstance(key, str) or not key.strip() for key in self.metric_values):
            raise ValueError("metric_values keys must not be empty")
        if any(not isinstance(key, str) or not key.strip() for key in self.dispersion):
            raise ValueError("dispersion keys must not be empty")
        if any(
            not isinstance(key, str) or not key.strip() or not isinstance(value, str) or not value.strip()
            for key, value in self.metric_artifact_refs.items()
        ):
            raise ValueError("metric_artifact_refs must contain non-empty strings")

        if self.artifact_path:
            _validate_artifact_path(self.artifact_path, self.research_run_id)

        if verification_status == EvidenceStatus.VERIFIED:
            self._validate_verified()

    @property
    def support_level(self) -> ScientificSupportLevel:
        """Experiment records are the only source of experiment-level support."""
        from .value_gate.schema import ScientificSupportLevel

        return ScientificSupportLevel.EXPERIMENT

    @property
    def is_verified(self) -> bool:
        from .value_gate.schema import EvidenceStatus

        return self.verification_status == EvidenceStatus.VERIFIED

    def _validate_verified(self) -> None:
        missing: list[str] = []
        for name in (
            "method_id",
            "baseline_id",
            "dataset_id",
            "dataset_source_uri",
            "dataset_source_hash",
            "analysis_method",
            "artifact_path",
        ):
            if not getattr(self, name).strip():
                missing.append(name)
        if not self.config_snapshot and not self.config_hash.strip():
            missing.append("config_snapshot or config_hash")
        if self.seed is None:
            missing.append("seed")
        if not self.metric_values:
            missing.append("metric_values")
        if set(self.metric_artifact_refs) != set(self.metric_values):
            missing.append("metric_artifact_refs for every metric")
        if not self.dispersion and self.run_count is None:
            missing.append("dispersion or run_count")
        if self.execution_status != ExperimentExecutionStatus.COMPLETED:
            raise ValueError("verified experiment evidence requires completed execution")
        if missing:
            raise ValueError(
                "verified experiment evidence is missing: " + ", ".join(missing)
            )
        prefix = f"{self.artifact_path}#"
        if any(not ref.startswith(prefix) for ref in self.metric_artifact_refs.values()):
            raise ValueError("metric values must be traceable to artifact_path")

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "research_run_id": self.research_run_id,
            "method_id": self.method_id,
            "baseline_id": self.baseline_id,
            "dataset_id": self.dataset_id,
            "dataset_source_uri": self.dataset_source_uri,
            "dataset_source_hash": self.dataset_source_hash,
            "config_snapshot": self.config_snapshot,
            "config_hash": self.config_hash,
            "seed": self.seed,
            "metric_values": self.metric_values,
            "dispersion": self.dispersion,
            "run_count": self.run_count,
            "analysis_method": self.analysis_method,
            "execution_status": self.execution_status.value,
            "verification_status": self.verification_status.value,
            "artifact_path": self.artifact_path,
            "metric_artifact_refs": self.metric_artifact_refs,
            "execution_mode": self.execution_mode,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExperimentEvidenceRecord":
        return cls(**data)

    @classmethod
    def from_json(cls, value: str) -> "ExperimentEvidenceRecord":
        return cls.from_dict(json.loads(value))


def _validate_measurements(
    values: dict[str, float], name: str, *, nonnegative: bool = False
) -> None:
    if not isinstance(values, dict):
        raise ValueError(f"{name} must be a dictionary")
    for value in values.values():
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{name} values must be finite numbers")
        if not math.isfinite(value):
            raise ValueError(f"{name} values must be finite numbers")
        if nonnegative and value < 0:
            raise ValueError(f"{name} values must not be negative")


def _validate_artifact_path(path: str, research_run_id: str) -> None:
    artifact = PurePath(path.replace("\\", "/"))
    if artifact.is_absolute() or artifact.anchor or ".." in artifact.parts:
        raise ValueError("artifact_path must be relative and stay within the run")
    if research_run_id not in artifact.parts:
        raise ValueError("artifact_path must include research_run_id")
