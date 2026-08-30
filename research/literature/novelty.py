"""Evidence-bound novelty-gap construction."""

from __future__ import annotations

from dataclasses import asdict, dataclass
from typing import Any

from ..value_gate.schema import (
    CandidateProblem,
    EvidenceBundle,
    EvidenceStatus,
    ScientificSupportLevel,
)
from .quality import LiteratureQualityReport


@dataclass(frozen=True)
class NoveltyGapReport:
    closest_prior_work_ids: tuple[str, ...]
    supported_gap: str
    candidate_difference: str
    evidence_ids: tuple[str, ...]
    confidence: float
    unsupported_claims: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class NoveltyGapBuilder:
    """Build only claims that can be traced to an EvidenceBundle."""

    def build(
        self,
        candidate: CandidateProblem,
        bundle: EvidenceBundle,
        quality: LiteratureQualityReport,
    ) -> NoveltyGapReport:
        usable = set(quality.usable_evidence_ids)
        verified = {
            item.evidence_id
            for item in bundle.items
            if item.evidence_id in usable
            and item.verification_status == EvidenceStatus.VERIFIED
            and item.kind == "literature"
        }
        prior_ids = tuple(
            evidence_id
            for evidence_id in candidate.closest_prior_work
            if evidence_id in verified
        )
        claim_ids = tuple(
            evidence_id
            for evidence_id in candidate.novelty_evidence_ids
            if evidence_id in verified
        )
        evidence_ids = tuple(dict.fromkeys(prior_ids + claim_ids))
        unsupported: list[str] = list(quality.unsupported_claims)
        if not prior_ids:
            unsupported.append("no verified closest prior work is available")
        missing_claim_ids = set(candidate.novelty_evidence_ids) - set(claim_ids)
        if missing_claim_ids:
            unsupported.append(
                "novelty claim references unavailable or unverified evidence_id(s): "
                + ", ".join(sorted(missing_claim_ids))
            )
        if candidate.difference.strip() and not candidate.hypothesis.strip():
            unsupported.append("candidate difference is not linked to a hypothesis")

        referenced_items = tuple(
            item for evidence_id in evidence_ids
            if (item := bundle.get(evidence_id)) is not None
        )
        weak_ids = tuple(
            item.evidence_id
            for item in referenced_items
            if not item.support_level.supports(ScientificSupportLevel.FULL_TEXT)
        )
        if candidate.difference.strip() and claim_ids and weak_ids:
            unsupported.append(
                "abstract/metadata evidence cannot establish a complete technical difference; "
                "full_text support is required for: " + ", ".join(weak_ids)
            )
        if candidate.gap.strip() and evidence_ids and weak_ids:
            unsupported.append(
                "abstract/metadata evidence cannot establish a complete novelty gap; "
                "full_text support is required"
            )
        if not candidate.difference.strip():
            unsupported.append("candidate technical difference is missing")

        referenced_ids = set(candidate.closest_prior_work + candidate.novelty_evidence_ids)
        pending_source = quality.search_status in {
            "failed",
            "partial",
        } or any(
            item.verification_status == EvidenceStatus.PENDING
            for item in bundle.items
            if item.evidence_id in referenced_ids
        )
        complete_requirements = bool(
            prior_ids
            and claim_ids
            and candidate.gap.strip()
            and candidate.difference.strip()
            and candidate.hypothesis.strip()
        )
        full_text_ready = bool(referenced_items) and not weak_ids and len(referenced_items) == len(evidence_ids)
        if not complete_requirements or pending_source or unsupported or not full_text_ready:
            status = "pending" if pending_source else "insufficient"
            gap = ""
            difference = ""
            confidence = 0.0
        else:
            status = "supported"
            gap = candidate.gap
            difference = candidate.difference if candidate.hypothesis.strip() else ""
            confidence = 0.6 if difference else 0.5
        return NoveltyGapReport(
            closest_prior_work_ids=prior_ids,
            supported_gap=gap,
            candidate_difference=difference,
            evidence_ids=evidence_ids,
            confidence=confidence,
            unsupported_claims=tuple(dict.fromkeys(unsupported)),
            status=status,
        )
