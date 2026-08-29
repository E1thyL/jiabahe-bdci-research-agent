"""Evidence-backed research-value screening."""

from .gate import ResearchValueGate
from .evidence import EvidenceCollector, FixtureEvidenceCollector
from .schema import (
    CandidateProblem,
    CriterionAssessment,
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    GateDecision,
    ValueGateDecision,
)

__all__ = [
    "CandidateProblem",
    "CriterionAssessment",
    "EvidenceBundle",
    "EvidenceItem",
    "EvidenceStatus",
    "EvidenceCollector",
    "FixtureEvidenceCollector",
    "GateDecision",
    "ResearchValueGate",
    "ValueGateDecision",
]
