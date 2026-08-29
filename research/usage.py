"""Pipeline-wide resource usage records.

This module records usage; it does not collect tokens from a model provider.
Callers must explicitly mark values as observed, estimated, or pending.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
import json
from pathlib import PurePath
from typing import Any, Iterable, Protocol


class ResearchPhase(StrEnum):
    VALUE_GATE = "value_gate"
    LITERATURE = "literature"
    METHOD_DESIGN = "method_design"
    EXPERIMENT_DESIGN = "experiment_design"
    DRAFTING = "drafting"
    INTERNAL_REVIEW = "internal_review"
    PUBLICATION_REVIEW = "publication_review"


class MeasurementStatus(StrEnum):
    OBSERVED = "observed"
    ESTIMATED = "estimated"
    PENDING = "pending"


_RESOURCE_FIELDS = (
    "input_tokens",
    "output_tokens",
    "tool_calls",
    "retry_count",
    "wall_time_ms",
    "reviewer_calls",
)


class UsageSink(Protocol):
    """Consumer for usage records; sinks may persist or aggregate them."""

    def record(self, record: "ResearchUsageRecord") -> None:
        ...


@dataclass(frozen=True)
class ResearchUsageRecord:
    """One resource measurement associated with a research run and artifact."""

    record_id: str
    research_run_id: str
    phase: ResearchPhase | str
    model: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    tool_calls: int | None = None
    retry_count: int | None = None
    wall_time_ms: int | None = None
    reviewer_calls: int | None = None
    artifact_path: str = ""
    measurement_status: MeasurementStatus | str = MeasurementStatus.OBSERVED

    def __post_init__(self) -> None:
        if not self.record_id.strip():
            raise ValueError("record_id must not be empty")
        if not self.research_run_id.strip():
            raise ValueError("research_run_id must not be empty")
        try:
            phase = ResearchPhase(self.phase)
        except ValueError as exc:
            raise ValueError(f"unsupported phase: {self.phase}") from exc
        try:
            status = MeasurementStatus(self.measurement_status)
        except ValueError as exc:
            raise ValueError(
                f"unsupported measurement_status: {self.measurement_status}"
            ) from exc
        object.__setattr__(self, "phase", phase)
        object.__setattr__(self, "measurement_status", status)

        if not self.artifact_path.strip():
            raise ValueError("artifact_path must not be empty")
        artifact = PurePath(self.artifact_path.replace("\\", "/"))
        if artifact.is_absolute() or artifact.anchor:
            raise ValueError("artifact_path must be relative")
        if self.research_run_id not in artifact.parts:
            raise ValueError("artifact_path must include research_run_id")

        missing = []
        for name in _RESOURCE_FIELDS:
            value = getattr(self, name)
            if value is not None and value < 0:
                raise ValueError(f"{name} cannot be negative")
            if status != MeasurementStatus.PENDING and value is None:
                missing.append(name)
        if missing:
            raise ValueError(
                "non-pending measurements require resource fields: "
                + ", ".join(missing)
            )

    def to_dict(self) -> dict[str, Any]:
        return {
            "record_id": self.record_id,
            "research_run_id": self.research_run_id,
            "phase": self.phase.value,
            "model": self.model,
            **{name: getattr(self, name) for name in _RESOURCE_FIELDS},
            "artifact_path": self.artifact_path,
            "measurement_status": self.measurement_status.value,
        }

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ResearchUsageRecord":
        return cls(**data)

    @classmethod
    def from_json(cls, value: str) -> "ResearchUsageRecord":
        return cls.from_dict(json.loads(value))


def make_phase_usage_record(
    *,
    phase: ResearchPhase | str,
    research_run_id: str,
    artifact_path: str | None = None,
    model: str = "",
    record_id: str | None = None,
    measurement_status: MeasurementStatus | str = MeasurementStatus.PENDING,
    **measurements: int | None,
) -> ResearchUsageRecord:
    """Create an explicit phase record, defaulting unknown measurements to pending."""
    normalized_phase = ResearchPhase(phase)
    path = artifact_path or f"artifacts/{research_run_id}/{normalized_phase.value}.json"
    return ResearchUsageRecord(
        record_id=record_id or f"usage-{research_run_id}-{normalized_phase.value}",
        research_run_id=research_run_id,
        phase=normalized_phase,
        model=model,
        artifact_path=path,
        measurement_status=measurement_status,
        **{name: measurements.get(name) for name in _RESOURCE_FIELDS},
    )


def emit_usage(
    sink: UsageSink | None,
    record: ResearchUsageRecord | None,
) -> None:
    """Send a record only when a caller explicitly supplied a sink."""
    if sink is not None and record is not None:
        sink.record(record)


def _totals(records: Iterable[ResearchUsageRecord]) -> dict[str, int]:
    result = {
        "total_input_tokens": 0,
        "total_output_tokens": 0,
        "total_tool_calls": 0,
        "total_retries": 0,
        "total_wall_time_ms": 0,
        "total_reviewer_calls": 0,
    }
    for record in records:
        result["total_input_tokens"] += record.input_tokens or 0
        result["total_output_tokens"] += record.output_tokens or 0
        result["total_tool_calls"] += record.tool_calls or 0
        result["total_retries"] += record.retry_count or 0
        result["total_wall_time_ms"] += record.wall_time_ms or 0
        result["total_reviewer_calls"] += record.reviewer_calls or 0
    return result


def aggregate_usage(records: Iterable[ResearchUsageRecord]) -> dict[str, Any]:
    """Aggregate records while preserving phase boundaries.

    Pending records contribute zero to numeric totals because they represent
    unknown measurements, not observed zero usage. Their status remains on the
    original records for downstream reporting.
    """
    records = tuple(records)
    by_phase: dict[str, dict[str, int]] = {}
    for phase in ResearchPhase:
        phase_records = (record for record in records if record.phase == phase)
        by_phase[phase.value] = _totals(phase_records)
    return {**_totals(records), "by_phase": by_phase}
