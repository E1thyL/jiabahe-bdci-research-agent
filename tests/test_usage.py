from __future__ import annotations

import json

import pytest

from research.usage import (
    MeasurementStatus,
    ResearchUsageRecord,
    aggregate_usage,
)
from research.value_gate import (
    CandidateProblem,
    EvidenceBundle,
    EvidenceItem,
    FixtureEvidenceCollector,
    ResearchValueGate,
)


class RecordingSink:
    def __init__(self) -> None:
        self.records = []

    def record(self, record) -> None:
        self.records.append(record)


def _record(**overrides) -> ResearchUsageRecord:
    values = dict(
        record_id="usage-001",
        research_run_id="research-001",
        phase="value_gate",
        model="model-name",
        input_tokens=1200,
        output_tokens=800,
        tool_calls=3,
        retry_count=0,
        wall_time_ms=4200,
        reviewer_calls=0,
        artifact_path="artifacts/research-001/value_gate.json",
        measurement_status="observed",
    )
    values.update(overrides)
    return ResearchUsageRecord(**values)


def test_normal_record_and_json_round_trip() -> None:
    record = _record()
    restored = ResearchUsageRecord.from_json(record.to_json())

    assert restored == record
    assert json.loads(record.to_json())["phase"] == "value_gate"


@pytest.mark.parametrize(
    "field",
    ["input_tokens", "output_tokens", "tool_calls", "retry_count", "wall_time_ms", "reviewer_calls"],
)
def test_negative_resource_values_are_rejected(field: str) -> None:
    with pytest.raises(ValueError, match="cannot be negative"):
        _record(**{field: -1})


def test_unknown_phase_and_missing_run_id_are_rejected() -> None:
    with pytest.raises(ValueError, match="unsupported phase"):
        _record(phase="unknown")
    with pytest.raises(ValueError, match="research_run_id"):
        _record(research_run_id="")


@pytest.mark.parametrize("status", ["observed", "estimated", "pending"])
def test_measurement_statuses_are_explicit(status: str) -> None:
    values = {} if status == "pending" else {
        "input_tokens": 1,
        "output_tokens": 2,
        "tool_calls": 0,
        "retry_count": 0,
        "wall_time_ms": 10,
        "reviewer_calls": 0,
    }
    record = _record(measurement_status=status, **values)
    assert record.measurement_status == MeasurementStatus(status)


def test_non_pending_measurements_cannot_silently_omit_tokens() -> None:
    with pytest.raises(ValueError, match="resource fields"):
        _record(input_tokens=None)


def test_pending_measurement_allows_empty_resource_fields() -> None:
    record = _record(
        input_tokens=None,
        output_tokens=None,
        tool_calls=None,
        retry_count=None,
        wall_time_ms=None,
        reviewer_calls=None,
        measurement_status="pending",
    )
    assert record.to_dict()["input_tokens"] is None


def test_estimated_measurement_can_leave_unknown_tokens_null() -> None:
    record = _record(
        input_tokens=None,
        output_tokens=None,
        tool_calls=1,
        wall_time_ms=25,
        measurement_status="estimated",
    )

    assert record.measurement_status == MeasurementStatus.ESTIMATED
    assert record.input_tokens is None
    assert record.tool_calls == 1


def test_artifact_path_must_be_relative_and_run_scoped() -> None:
    with pytest.raises(ValueError, match="relative"):
        _record(artifact_path="C:/tmp/value_gate.json")
    with pytest.raises(ValueError, match="include research_run_id"):
        _record(artifact_path="artifacts/other-run/value_gate.json")


def test_aggregate_usage_preserves_phase_totals() -> None:
    records = (
        _record(),
        _record(
            record_id="usage-002",
            phase="literature",
            input_tokens=100,
            output_tokens=50,
            tool_calls=2,
            wall_time_ms=300,
            artifact_path="artifacts/research-001/literature.json",
        ),
        _record(
            record_id="usage-003",
            phase="drafting",
            input_tokens=None,
            output_tokens=None,
            tool_calls=None,
            retry_count=None,
            wall_time_ms=None,
            reviewer_calls=None,
            measurement_status="pending",
            artifact_path="artifacts/research-001/drafting.json",
        ),
    )
    result = aggregate_usage(records)

    assert result["total_input_tokens"] == 1300
    assert result["total_output_tokens"] == 850
    assert result["total_tool_calls"] == 5
    assert result["by_phase"]["value_gate"]["total_wall_time_ms"] == 4200
    assert result["by_phase"]["literature"]["total_input_tokens"] == 100
    assert result["by_phase"]["drafting"]["total_input_tokens"] == 0


def test_aggregate_usage_counts_requests_by_phase_and_preserves_unknown() -> None:
    records = (
        _record(request_count=1),
        _record(record_id="usage-002", phase="literature", request_count=2,
                artifact_path="artifacts/research-001/literature.json"),
        _record(record_id="usage-003", phase="drafting", request_count=None,
                input_tokens=None, output_tokens=None, tool_calls=None,
                retry_count=None, wall_time_ms=None, reviewer_calls=None,
                measurement_status="pending", artifact_path="artifacts/research-001/drafting.json"),
    )
    result = aggregate_usage(records)
    assert result["total_request_count"] == 3
    assert result["by_phase"]["value_gate"]["total_request_count"] == 1
    assert result["by_phase"]["literature"]["total_request_count"] == 2
    assert result["by_phase"]["drafting"]["total_request_count"] is None


def test_aggregate_usage_keeps_zero_and_all_unknown_distinct() -> None:
    zero = _record(request_count=0)
    unknown = _record(record_id="usage-unknown", request_count=None)
    assert aggregate_usage((zero,))["total_request_count"] == 0
    assert aggregate_usage((unknown,))["total_request_count"] is None


def _candidate() -> CandidateProblem:
    return CandidateProblem(
        problem_statement="A measurable research problem",
        research_object="research agents",
        hypothesis="Evidence improves quality",
        topic="context_engineering",
        significance_evidence_ids=("paper-1",),
        closest_prior_work=("paper-1",),
        novelty_evidence_ids=("paper-1",),
        gap="An unmeasured gap",
        difference="A measurable difference",
        datasets=("tasks",),
        baselines=("baseline",),
        metrics=("quality",),
        feasibility_evidence_ids=("paper-1",),
    )


def _evidence() -> EvidenceBundle:
    return EvidenceBundle((EvidenceItem(
        "paper-1", "paper://1", "Prior Work", ("Author",), 2025,
        "Venue", "evidence", "prior_work", source_hash="hash-1",
    ),))


def test_evidence_collector_records_pending_literature_usage() -> None:
    sink = RecordingSink()
    collector = FixtureEvidenceCollector(_evidence())

    collector.collect(_candidate(), usage_sink=sink, research_run_id="research-001")

    record = sink.records[0]
    assert record.phase.value == "literature"
    assert record.measurement_status == MeasurementStatus.PENDING
    assert record.artifact_path == "artifacts/research-001/literature.json"
    assert record.input_tokens is None


@pytest.mark.parametrize("status", ["observed", "estimated"])
def test_collector_accepts_explicit_resource_status(status: str) -> None:
    sink = RecordingSink()
    record = _record(
        phase="literature",
        measurement_status=status,
        artifact_path="artifacts/research-001/literature.json",
    )

    FixtureEvidenceCollector(_evidence()).collect(
        _candidate(), usage_sink=sink, usage_record=record
    )

    assert sink.records == [record]


def test_gate_records_value_gate_usage_without_changing_decision() -> None:
    sink = RecordingSink()
    result = ResearchValueGate().evaluate(
        _candidate(),
        _evidence(),
        usage_sink=sink,
        research_run_id="research-001",
    )

    assert result.decision.value == "go"
    assert sink.records[0].phase.value == "value_gate"
    assert sink.records[0].measurement_status == MeasurementStatus.PENDING
    assert "research-001" in sink.records[0].artifact_path


def test_usage_sink_is_optional_for_existing_calls() -> None:
    result = ResearchValueGate().evaluate(_candidate(), _evidence())

    assert result.decision.value == "go"


def test_pending_usage_is_not_counted_as_observed_consumption() -> None:
    result = aggregate_usage(
        [_record(), _record(
            record_id="usage-pending",
            input_tokens=None,
            output_tokens=None,
            tool_calls=None,
            retry_count=None,
            wall_time_ms=None,
            reviewer_calls=None,
            measurement_status="pending",
        )]
    )

    assert result["total_input_tokens"] == 1200
    assert result["total_output_tokens"] == 800
