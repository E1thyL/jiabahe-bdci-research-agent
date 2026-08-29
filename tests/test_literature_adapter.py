from __future__ import annotations

import pytest

from research.usage import MeasurementStatus
from research.value_gate import (
    AdapterEvidenceCollector,
    CandidateProblem,
    EvidenceBundle,
    EvidenceItem,
    FixtureEvidenceCollector,
    ResearchValueGate,
)
from research.literature import (
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
    ReplayLiteratureSource,
)


def _candidate() -> CandidateProblem:
    return CandidateProblem(
        problem_statement="fixture query",
        research_object="research agents",
        hypothesis="evidence improves quality",
        topic="context_engineering",
        significance_evidence_ids=("replay:PLACEHOLDER",),
        closest_prior_work=("replay:PLACEHOLDER",),
        novelty_evidence_ids=("replay:PLACEHOLDER",),
        gap="an observed gap",
        difference="a measurable difference",
        datasets=("tasks",),
        baselines=("baseline",),
        metrics=("quality",),
        feasibility_evidence_ids=("replay:PLACEHOLDER",),
    )


def _record() -> LiteratureRecord:
    return LiteratureRecord(
        source_uri="https://example.test/paper-1",
        title="A Fixture Prior Work",
        authors=("Author One",),
        year=2025,
        venue="FixtureConf",
        excerpt="A directly sourced excerpt.",
        evidence_type="prior_work",
    )


def test_replay_search_maps_records_and_query() -> None:
    source = ReplayLiteratureSource({"fixture query": (_record(),)})

    result = source.search(_candidate(), {"query": "fixture query"})
    bundle = result.to_evidence_bundle()

    assert result.status == LiteratureSearchStatus.SUCCESS
    assert result.query == "fixture query"
    assert result.candidate_problem == "fixture query"
    assert len(bundle.items) == 1
    assert bundle.items[0].source_uri == "https://example.test/paper-1"
    assert bundle.items[0].evidence_type == "prior_work"


def test_replay_source_hash_and_evidence_id_are_stable() -> None:
    source = ReplayLiteratureSource({"fixture query": (_record(),)})

    first = source.search(_candidate()).to_evidence_bundle().items[0]
    second = source.search(_candidate()).to_evidence_bundle().items[0]

    assert first.source_hash == second.source_hash
    assert first.evidence_id == second.evidence_id


def test_invalid_adapter_records_are_rejected() -> None:
    with pytest.raises(ValueError, match="source_uri"):
        LiteratureSearchResult(
            "fixture query", "fixture query", "replay",
            (LiteratureRecord("", "Title", (), 2025, "Venue", "Excerpt", "prior_work"),),
        ).to_evidence_bundle()

    item = EvidenceItem(
        "duplicate", "paper://1", "Paper", (), 2025, "Venue", "Excerpt",
        "prior_work", source_hash="hash-1",
    )
    with pytest.raises(ValueError, match="must be unique"):
        EvidenceBundle((item, item))


def test_pending_literature_cannot_support_novelty() -> None:
    pending = LiteratureRecord(
        _record().source_uri, _record().title, _record().authors, _record().year,
        _record().venue, _record().excerpt, _record().evidence_type,
        verification_status="pending",
    )
    source = ReplayLiteratureSource({"fixture query": (pending,)})
    bundle = source.search(_candidate()).to_evidence_bundle()
    evidence_id = bundle.items[0].evidence_id
    candidate = _candidate()
    candidate = CandidateProblem(
        **{**candidate.__dict__, "significance_evidence_ids": (evidence_id,),
           "closest_prior_work": (evidence_id,), "novelty_evidence_ids": (evidence_id,),
           "feasibility_evidence_ids": (evidence_id,)}
    )

    result = ResearchValueGate().evaluate(candidate, bundle)

    assert result.novelty.score == 0
    assert result.decision.value == "revise"


def test_empty_and_failed_search_results_are_distinct() -> None:
    empty = ReplayLiteratureSource({"empty": ()}).search(_candidate(), {"query": "empty"})
    failed = ReplayLiteratureSource({}, failures={"failed": "source unavailable"}).search(
        _candidate(), {"query": "failed"}
    )

    assert empty.status == LiteratureSearchStatus.EMPTY
    assert failed.status == LiteratureSearchStatus.FAILED
    assert failed.failure_reason == "source unavailable"
    assert empty.to_evidence_bundle().items == ()
    assert failed.to_evidence_bundle().items == ()


def test_adapter_collector_feeds_gate_and_records_pending_usage() -> None:
    source = ReplayLiteratureSource({"fixture query": (_record(),)})
    collector = AdapterEvidenceCollector(source)
    sink = []
    candidate = _candidate()

    class Sink:
        def record(self, record) -> None:
            sink.append(record)

    bundle = collector.collect(
        candidate,
        topic_config={"query": "fixture query"},
        usage_sink=Sink(),
        research_run_id="research-001",
    )
    evidence_id = bundle.items[0].evidence_id
    candidate = CandidateProblem(
        **{**candidate.__dict__, "significance_evidence_ids": (evidence_id,),
           "closest_prior_work": (evidence_id,), "novelty_evidence_ids": (evidence_id,),
           "feasibility_evidence_ids": (evidence_id,)}
    )
    decision = ResearchValueGate().evaluate(candidate, bundle)

    assert decision.decision.value == "go"
    assert sink[0].measurement_status == MeasurementStatus.PENDING
    assert sink[0].phase.value == "literature"
    assert "research-001" in sink[0].artifact_path


def test_collector_without_adapter_remains_compatible() -> None:
    item = EvidenceItem(
        "fixture:1", "paper://1", "Paper", (), 2025, "Venue", "Excerpt",
        "prior_work", source_hash="hash-1",
    )
    assert FixtureEvidenceCollector(EvidenceBundle((item,))).collect(_candidate()).items == (item,)
