"""Serializable schemas for the staged Research Value Gate."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from enum import StrEnum
import json
from functools import total_ordering
from typing import Any


class EvidenceStatus(StrEnum):
    VERIFIED = "verified"
    PENDING = "pending"
    INSUFFICIENT = "insufficient"


class GateDecision(StrEnum):
    GO = "go"
    REVISE = "revise"
    NO_GO = "no_go"


@total_ordering
class ScientificSupportLevel(StrEnum):
    """Strength of the scientific support carried by an evidence item.

    This is deliberately separate from :class:`EvidenceStatus`: a verified
    provenance record can still provide only metadata-level support.
    """

    METADATA = "metadata"
    ABSTRACT = "abstract"
    FULL_TEXT = "full_text"
    EXPERIMENT = "experiment"

    @property
    def rank(self) -> int:
        return ("metadata", "abstract", "full_text", "experiment").index(
            self.value
        )

    def __lt__(self, other: object) -> bool:
        if isinstance(other, str):
            other = type(self)(other)
        if not isinstance(other, type(self)):
            return NotImplemented
        return self.rank < other.rank

    def supports(self, required: "ScientificSupportLevel | str") -> bool:
        """Return whether this level is at least as strong as *required*."""
        return self >= type(self)(required)


@dataclass(frozen=True)
class CandidateProblem:
    """A candidate research problem before evidence-backed screening."""

    problem_statement: str
    research_object: str = ""
    hypothesis: str = ""
    topic: str = ""
    significance_evidence_ids: tuple[str, ...] = ()
    closest_prior_work: tuple[str, ...] = ()
    novelty_evidence_ids: tuple[str, ...] = ()
    gap: str = ""
    difference: str = ""
    datasets: tuple[str, ...] = ()
    baselines: tuple[str, ...] = ()
    metrics: tuple[str, ...] = ()
    feasibility_evidence_ids: tuple[str, ...] = ()
    expected_contribution: tuple[str, ...] = ()


@dataclass(frozen=True)
class EvidenceItem:
    """A provenance-bearing item used by a gate judgment."""

    evidence_id: str
    source_uri: str
    title: str
    authors: tuple[str, ...]
    year: int
    venue: str
    excerpt: str
    evidence_type: str
    verification_status: EvidenceStatus = EvidenceStatus.VERIFIED
    source_hash: str = ""
    support_level: ScientificSupportLevel = ScientificSupportLevel.METADATA

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "verification_status", EvidenceStatus(self.verification_status)
        )
        try:
            support_level = ScientificSupportLevel(self.support_level)
        except ValueError as exc:
            raise ValueError(
                f"unsupported scientific support level: {self.support_level}"
            ) from exc
        object.__setattr__(self, "support_level", support_level)
        if not self.evidence_id.strip():
            raise ValueError("evidence_id must not be empty")
        if not self.source_uri.strip() or not self.title.strip():
            raise ValueError("source_uri and title must not be empty")
        if not self.source_hash.strip():
            raise ValueError("source_hash must not be empty")
        if self.evidence_type not in {
            "prior_work",
            "limitation",
            "dataset",
            "baseline",
            "metric",
        }:
            raise ValueError(f"unsupported evidence_type: {self.evidence_type}")
        if support_level == ScientificSupportLevel.EXPERIMENT:
            raise ValueError(
                "EvidenceItem cannot use experiment support level; "
                "use ExperimentEvidenceRecord"
            )

    @property
    def kind(self) -> str:
        """Compatibility view used by the first Value Gate implementation."""
        return "literature" if self.evidence_type in {"prior_work", "limitation"} else self.evidence_type

    @property
    def status(self) -> EvidenceStatus:
        """Compatibility view for the renamed verification field."""
        return self.verification_status


@dataclass(frozen=True)
class EvidenceBundle:
    """A validated, offline-collected set of evidence items."""

    items: tuple[EvidenceItem, ...] = ()

    def __post_init__(self) -> None:
        ids = [item.evidence_id for item in self.items]
        if len(ids) != len(set(ids)):
            raise ValueError("evidence_id values must be unique")

    def get(self, evidence_id: str) -> EvidenceItem | None:
        return next((item for item in self.items if item.evidence_id == evidence_id), None)

    def ids(self) -> set[str]:
        return {item.evidence_id for item in self.items}


@dataclass(frozen=True)
class CriterionAssessment:
    score: int
    evidence_ids: tuple[str, ...]
    reasoning: str
    confidence: float

    def __post_init__(self) -> None:
        if not 0 <= self.score <= 5:
            raise ValueError("score must be between 0 and 5")
        if not 0 <= self.confidence <= 1:
            raise ValueError("confidence must be between 0 and 1")


@dataclass(frozen=True)
class ValueGateDecision:
    """Decision plus stage-specific evidence state and reviewer objections."""

    problem_statement: str
    significance: CriterionAssessment
    novelty: CriterionAssessment
    technical_feasibility: CriterionAssessment
    expected_contribution: tuple[str, ...]
    reviewer_objections: tuple[str, ...]
    literature: dict[str, Any]
    experiment: dict[str, Any]
    decision: GateDecision

    def to_dict(self) -> dict[str, Any]:
        return _jsonable(asdict(self))

    def to_json(self) -> str:
        return json.dumps(self.to_dict(), ensure_ascii=False, indent=2, sort_keys=True)


def _jsonable(value: Any) -> Any:
    if isinstance(value, StrEnum):
        return value.value
    if isinstance(value, tuple):
        return [_jsonable(item) for item in value]
    if isinstance(value, dict):
        return {key: _jsonable(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_jsonable(item) for item in value]
    return value
