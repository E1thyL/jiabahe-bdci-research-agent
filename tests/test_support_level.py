from __future__ import annotations

import json

import pytest

from research.literature import LiteratureRecord, LiteratureSearchResult
from research.value_gate import EvidenceItem, ScientificSupportLevel


def _item(**overrides) -> EvidenceItem:
    values = dict(
        evidence_id="paper:1",
        source_uri="https://example.test/paper",
        title="A Paper",
        authors=("Author",),
        year=2025,
        venue="Fixture Venue",
        excerpt="An excerpt.",
        evidence_type="prior_work",
        source_hash="hash-1",
    )
    values.update(overrides)
    return EvidenceItem(**values)


def test_support_levels_are_ordered_and_normalized() -> None:
    assert (
        ScientificSupportLevel.METADATA
        < ScientificSupportLevel.ABSTRACT
        < ScientificSupportLevel.FULL_TEXT
        < ScientificSupportLevel.EXPERIMENT
    )
    assert ScientificSupportLevel("abstract") is ScientificSupportLevel.ABSTRACT
    assert ScientificSupportLevel.FULL_TEXT.supports("abstract")
    assert not ScientificSupportLevel.ABSTRACT.supports("full_text")


def test_legacy_evidence_defaults_to_conservative_metadata_support() -> None:
    item = _item()

    assert item.support_level is ScientificSupportLevel.METADATA
    assert json.loads(json.dumps(item.support_level)) == "metadata"


def test_evidence_item_accepts_explicit_support_level() -> None:
    item = _item(support_level="full_text")

    assert item.support_level is ScientificSupportLevel.FULL_TEXT


@pytest.mark.parametrize("value", ["unknown", 1, None])
def test_unknown_support_level_is_rejected(value: object) -> None:
    with pytest.raises(ValueError, match="unsupported scientific support level"):
        _item(support_level=value)


def test_experiment_support_requires_experiment_record() -> None:
    with pytest.raises(ValueError, match="use ExperimentEvidenceRecord"):
        _item(support_level=ScientificSupportLevel.EXPERIMENT)


def test_literature_adapter_propagates_support_level_without_changing_identity() -> None:
    base = dict(
        source_uri="https://example.test/paper",
        title="A Paper",
        authors=("Author",),
        year=2025,
        venue="Fixture Venue",
        excerpt="An excerpt.",
        evidence_type="prior_work",
    )
    metadata_item = LiteratureSearchResult(
        "problem", "query", "fixture",
        (LiteratureRecord(**base),),
    ).to_evidence_bundle().items[0]
    full_text_item = LiteratureSearchResult(
        "problem", "query", "fixture",
        (LiteratureRecord(**base, support_level="full_text"),),
    ).to_evidence_bundle().items[0]

    assert metadata_item.support_level is ScientificSupportLevel.METADATA
    assert full_text_item.support_level is ScientificSupportLevel.FULL_TEXT
    assert metadata_item.source_hash == full_text_item.source_hash
    assert metadata_item.evidence_id == full_text_item.evidence_id
