"""Conservative, offline literature quality screening."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import re
from typing import Any
from urllib.parse import urlparse

from .protocol import LiteratureSearchResult, LiteratureSearchStatus
from ..value_gate.schema import CandidateProblem, EvidenceBundle, EvidenceItem, EvidenceStatus

_HASH_RE = re.compile(r"^[0-9a-f]{64}$")


@dataclass(frozen=True)
class LiteratureQualityReport:
    usable_evidence_ids: tuple[str, ...]
    excluded_evidence_ids: tuple[str, ...]
    source_quality: dict[str, dict[str, Any]]
    completeness: dict[str, dict[str, Any]]
    limitations: tuple[str, ...]
    unsupported_claims: tuple[str, ...]
    search_status: str | None = None
    failure_reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class LiteratureQualityFilter:
    """Classify source records without upgrading weak evidence."""

    def evaluate(
        self,
        candidate: CandidateProblem,
        bundle: EvidenceBundle,
        search_result: LiteratureSearchResult | None = None,
    ) -> LiteratureQualityReport:
        del candidate
        usable: list[str] = []
        excluded: list[str] = []
        source_quality: dict[str, dict[str, Any]] = {}
        completeness: dict[str, dict[str, Any]] = {}
        limitations: list[str] = []
        unsupported: list[str] = []

        for item in bundle.items:
            checks = {
                "source_uri_valid": _valid_uri(item.source_uri),
                "title_present": bool(item.title.strip()),
                "excerpt_available": bool(item.excerpt.strip()),
                "source_hash_valid": bool(_HASH_RE.fullmatch(item.source_hash)),
                "evidence_id_parseable": _parseable_id(item.evidence_id),
                "year_present": item.year > 0,
                "venue_present": bool(item.venue.strip()),
                "verification_status_explicit": isinstance(
                    item.verification_status, EvidenceStatus
                ),
            }
            completeness[item.evidence_id] = checks
            source_quality[item.evidence_id] = {
                "verification_status": item.verification_status.value,
                "evidence_type": item.evidence_type,
                "metadata_only": not checks["excerpt_available"],
            }
            required = (
                "source_uri_valid",
                "title_present",
                "excerpt_available",
                "source_hash_valid",
                "evidence_id_parseable",
            )
            if all(checks[name] for name in required):
                usable.append(item.evidence_id)
            else:
                excluded.append(item.evidence_id)
            if not checks["year_present"]:
                limitations.append(f"{item.evidence_id}: year is missing")
            if not checks["venue_present"]:
                limitations.append(f"{item.evidence_id}: venue is missing")
            if item.verification_status != EvidenceStatus.VERIFIED:
                limitations.append(
                    f"{item.evidence_id}: evidence status is {item.verification_status.value}"
                )
            if item.evidence_type in {"prior_work", "limitation"} and not item.excerpt.strip():
                unsupported.append(
                    f"{item.evidence_id}: metadata alone cannot support a technical claim"
                )

        return LiteratureQualityReport(
            usable_evidence_ids=tuple(usable),
            excluded_evidence_ids=tuple(excluded),
            source_quality=source_quality,
            completeness=completeness,
            limitations=tuple(dict.fromkeys(limitations)),
            unsupported_claims=tuple(dict.fromkeys(unsupported)),
            search_status=(search_result.status.value if search_result else None),
            failure_reason=(search_result.failure_reason if search_result else None),
        )


def _valid_uri(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme in {"http", "https"} and bool(parsed.netloc)


def _parseable_id(value: str) -> bool:
    return bool(value.strip()) and ":" in value and all(value.split(":", 1))
