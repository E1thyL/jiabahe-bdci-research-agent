"""Evidence-backed research-value screening."""

from .gate import ResearchValueGate
from .evidence import EvidenceCollector, FixtureEvidenceCollector
from .evidence import AdapterEvidenceCollector
from .schema import (
    CandidateProblem,
    CriterionAssessment,
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    GateDecision,
    ScientificSupportLevel,
    ValueGateDecision,
)

__all__ = [
    "CandidateProblem",
    "CriterionAssessment",
    "EvidenceBundle",
    "EvidenceItem",
    "EvidenceStatus",
    "ScientificSupportLevel",
    "EvidenceCollector",
    "FixtureEvidenceCollector",
    "AdapterEvidenceCollector",
    "GateDecision",
    "ResearchValueGate",
    "ValueGateDecision",
]
