from __future__ import annotations

from dataclasses import replace

from research.literature import (
    LiteratureQualityFilter,
    LiteratureRecord,
    LiteratureSearchResult,
    LiteratureSearchStatus,
    NoveltyGapBuilder,
    ReplayLiteratureSource,
)
from research.value_gate import CandidateProblem, EvidenceBundle, EvidenceItem, ResearchValueGate


def _record(**overrides) -> LiteratureRecord:
    values = dict(
        source_uri="https://example.test/paper",
        title="Prior Work",
        authors=("Author",),
        year=2025,
        venue="Fixture Venue",
        excerpt="The abstract describes a bounded method.",
        evidence_type="prior_work",
    )
    values.update(overrides)
    return LiteratureRecord(**values)


def _candidate() -> CandidateProblem:
    return CandidateProblem(
        problem_statement="fixture problem",
        research_object="research agents",
        hypothesis="the proposed method improves quality",
        topic="context_engineering",
        gap="Prior work does not measure evidence retention.",
        difference="We measure evidence retention and token cost.",
        datasets=("fixture-dataset",),
        baselines=("fixture-baseline",),
        metrics=("quality",),
    )


def _bundle_candidate(bundle: EvidenceBundle) -> CandidateProblem:
    ids = tuple(item.evidence_id for item in bundle.items)
    return replace(
        _candidate(),
        significance_evidence_ids=ids,
        closest_prior_work=ids,
        novelty_evidence_ids=ids,
        feasibility_evidence_ids=ids,
    )


def test_complete_replay_snapshot_quality_and_novelty_end_to_end() -> None:
    candidate = _candidate()
    result = ReplayLiteratureSource({"fixture query": (_record(),)}).search(
        candidate, {"query": "fixture query"}
    )
    bundle = result.to_evidence_bundle()
    candidate = _bundle_candidate(bundle)
    quality = LiteratureQualityFilter().evaluate(candidate, bundle, result)
    novelty = NoveltyGapBuilder().build(candidate, bundle, quality)
    decision = ResearchValueGate().evaluate(candidate, bundle)

    assert quality.usable_evidence_ids == tuple(item.evidence_id for item in bundle.items)
    assert novelty.status == "supported"
    assert novelty.closest_prior_work_ids == quality.usable_evidence_ids
    assert novelty.evidence_ids == quality.usable_evidence_ids
    assert decision.decision.value == "go"


def test_quality_reports_missing_year_and_venue_without_no_go() -> None:
    item = EvidenceBundle((_item(year=0, venue=""),))
    report = LiteratureQualityFilter().evaluate(_candidate(), item)

    assert report.usable_evidence_ids
    assert any("year is missing" in value for value in report.limitations)
    assert any("venue is missing" in value for value in report.limitations)


def _item(**overrides) -> EvidenceItem:
    values = dict(
        evidence_id="fixture:aaaaaaaaaaaaaaaa",
        source_uri="https://example.test/paper",
        title="Prior Work",
        authors=("Author",),
        year=2025,
        venue="Venue",
        excerpt="Abstract excerpt",
        evidence_type="prior_work",
        source_hash="a" * 64,
    )
    values.update(overrides)
    return EvidenceItem(**values)


def test_title_only_record_is_excluded_and_cannot_form_technical_gap() -> None:
    bundle = EvidenceBundle((_item(excerpt=""),))
    candidate = replace(
        _candidate(),
        closest_prior_work=(bundle.items[0].evidence_id,),
        novelty_evidence_ids=(bundle.items[0].evidence_id,),
    )
    quality = LiteratureQualityFilter().evaluate(candidate, bundle)
    novelty = NoveltyGapBuilder().build(candidate, bundle, quality)

    assert quality.excluded_evidence_ids == (bundle.items[0].evidence_id,)
    assert novelty.status == "insufficient"
    assert novelty.supported_gap == ""
    assert novelty.candidate_difference == ""


def test_unverified_evidence_is_usable_for_audit_but_not_novelty() -> None:
    bundle = EvidenceBundle((_item(verification_status="pending"),))
    candidate = replace(
        _candidate(),
        closest_prior_work=(bundle.items[0].evidence_id,),
        novelty_evidence_ids=(bundle.items[0].evidence_id,),
    )
    quality = LiteratureQualityFilter().evaluate(candidate, bundle)
    novelty = NoveltyGapBuilder().build(candidate, bundle, quality)

    assert quality.usable_evidence_ids == (bundle.items[0].evidence_id,)
    assert novelty.closest_prior_work_ids == ()
    assert novelty.status == "pending"


def test_search_empty_and_partial_states_are_reported_separately() -> None:
    empty = LiteratureSearchResult("problem", "q", "openalex", status="empty")
    partial = LiteratureSearchResult("problem", "q", "openalex", status="partial")
    empty_report = LiteratureQualityFilter().evaluate(_candidate(), EvidenceBundle(), empty)
    partial_report = LiteratureQualityFilter().evaluate(_candidate(), EvidenceBundle(), partial)

    assert empty_report.search_status == LiteratureSearchStatus.EMPTY.value
    assert partial_report.search_status == LiteratureSearchStatus.PARTIAL.value
    assert empty_report.failure_reason is None


def test_novelty_unknown_evidence_id_is_explicitly_unsupported() -> None:
    candidate = replace(
        _candidate(),
        closest_prior_work=("missing:1",),
        novelty_evidence_ids=("missing:1",),
    )
    quality = LiteratureQualityFilter().evaluate(candidate, EvidenceBundle())
    novelty = NoveltyGapBuilder().build(candidate, EvidenceBundle(), quality)

    assert novelty.status == "insufficient"
    assert any("unavailable" in value for value in novelty.unsupported_claims)
