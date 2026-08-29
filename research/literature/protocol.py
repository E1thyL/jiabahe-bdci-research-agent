"""Protocol and transport-neutral schemas for literature sources."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Any, Protocol

from ..value_gate.schema import CandidateProblem, EvidenceBundle, EvidenceItem, EvidenceStatus


class LiteratureSearchStatus(StrEnum):
    SUCCESS = "success"
    EMPTY = "empty"
    PARTIAL = "partial"
    FAILED = "failed"


@dataclass(frozen=True)
class LiteratureRecord:
    """Raw source record owned by an adapter before EvidenceItem materialization."""

    source_uri: str
    title: str
    authors: tuple[str, ...]
    year: int
    venue: str
    excerpt: str
    evidence_type: str
    verification_status: EvidenceStatus = EvidenceStatus.VERIFIED

    def __post_init__(self) -> None:
        object.__setattr__(self, "verification_status", EvidenceStatus(self.verification_status))


@dataclass(frozen=True)
class LiteratureSearchResult:
    """Search response retaining query, source, status, and raw records."""

    candidate_problem: str
    query: str
    source_name: str
    records: tuple[LiteratureRecord, ...] = ()
    status: LiteratureSearchStatus = LiteratureSearchStatus.SUCCESS
    failure_reason: str | None = None
    artifact_path: str | None = None
    raw_response: dict[str, Any] | None = None

    def to_evidence_bundle(self) -> EvidenceBundle:
        """Materialize adapter-owned records into provenance-bearing evidence."""
        items = tuple(
            EvidenceItem(
                evidence_id=f"{self.source_name}:{_stable_hash(record)[:16]}",
                source_uri=record.source_uri,
                title=record.title,
                authors=record.authors,
                year=record.year,
                venue=record.venue,
                excerpt=record.excerpt,
                evidence_type=record.evidence_type,
                verification_status=record.verification_status,
                source_hash=_stable_hash(record),
            )
            for record in self.records
        )
        return EvidenceBundle(items)


class LiteratureSourceAdapter(Protocol):
    """Single-source interface; implementations return source-owned records."""

    def search(
        self,
        candidate: CandidateProblem,
        topic_config: dict[str, Any] | None = None,
    ) -> LiteratureSearchResult:
        ...


def _stable_hash(record: LiteratureRecord) -> str:
    import hashlib
    import json

    payload = {
        "source_uri": record.source_uri,
        "title": record.title,
        "authors": list(record.authors),
        "year": record.year,
        "venue": record.venue,
        "excerpt": record.excerpt,
        "evidence_type": record.evidence_type,
        "verification_status": record.verification_status.value,
    }
    return hashlib.sha256(
        json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()
