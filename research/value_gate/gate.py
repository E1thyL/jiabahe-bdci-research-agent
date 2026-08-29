"""Deterministic, evidence-backed Research Value Gate."""

from __future__ import annotations

from .evidence import EvidenceIndex
from .policies import topic_policy
from .schema import (
    CandidateProblem,
    CriterionAssessment,
    EvidenceBundle,
    EvidenceItem,
    EvidenceStatus,
    GateDecision,
    ValueGateDecision,
)


class ResearchValueGate:
    """Screen a candidate before method and experiment design.

    This class deliberately does not search, call an LLM, or claim experimental
    validation. Literature evidence is required for novelty; experiment status
    remains ``pending`` until a later Publication Gate evaluates results.
    """

    def evaluate(
        self,
        candidate: CandidateProblem,
        evidence: EvidenceBundle | tuple[EvidenceItem, ...] = (),
    ) -> ValueGateDecision:
        topic_policy(candidate.topic)
        index = EvidenceIndex(evidence)
        objections: list[str] = []

        referenced_ids = set(
            candidate.significance_evidence_ids
            + candidate.novelty_evidence_ids
            + candidate.feasibility_evidence_ids
        )
        missing_ids = sorted(referenced_ids - index.ids)
        if missing_ids:
            objections.append(
                "assessment references unknown evidence_id(s): " + ", ".join(missing_ids)
            )

        significance_ids = candidate.significance_evidence_ids
        significance_ok = bool(significance_ids) and index.has_verified_literature(
            significance_ids
        )
        if not significance_ok:
            objections.append("significance lacks verified literature evidence")

        novelty_ok = (
            bool(candidate.closest_prior_work)
            and bool(candidate.gap.strip())
            and bool(candidate.difference.strip())
            and index.has_verified_literature(candidate.novelty_evidence_ids)
        )
        if not candidate.closest_prior_work:
            objections.append("closest prior work is missing")
        if not novelty_ok and candidate.closest_prior_work:
            objections.append("novelty gap lacks sufficient verified evidence")

        feasibility_ok = (
            bool(candidate.datasets)
            and bool(candidate.baselines)
            and bool(candidate.metrics)
            and bool(candidate.feasibility_evidence_ids)
            and index.has_verified_literature(candidate.feasibility_evidence_ids)
        )
        if not feasibility_ok:
            objections.append("datasets, baselines, and metrics must all be executable")

        if not candidate.research_object.strip():
            objections.append("research object is missing")
        if not candidate.hypothesis.strip():
            objections.append("research hypothesis is missing")
        if not candidate.problem_statement.strip():
            objections.append("problem statement is missing")

        significance = CriterionAssessment(
            score=4 if significance_ok else 0,
            evidence_ids=significance_ids,
            reasoning="Verified literature supports the stated research importance."
            if significance_ok
            else "No verified literature evidence is attached.",
            confidence=0.8 if significance_ok else 0.0,
        )
        novelty = CriterionAssessment(
            score=4 if novelty_ok else 0,
            evidence_ids=candidate.novelty_evidence_ids,
            reasoning="Prior work, gap, difference, and verified literature are present."
            if novelty_ok
            else "Novelty cannot be concluded before prior-work evidence is verified.",
            confidence=0.78 if novelty_ok else 0.0,
        )
        feasibility = CriterionAssessment(
            score=4 if feasibility_ok else 0,
            evidence_ids=candidate.feasibility_evidence_ids,
            reasoning="Datasets, baselines, and metrics are specified."
            if feasibility_ok
            else "An executable dataset, baseline, and metric set is incomplete.",
            confidence=0.75 if feasibility_ok else 0.0,
        )

        if not candidate.research_object.strip() or not candidate.hypothesis.strip():
            decision = GateDecision.REVISE
        elif not candidate.problem_statement.strip():
            decision = GateDecision.NO_GO
        elif significance_ok and novelty_ok and feasibility_ok and not objections:
            decision = GateDecision.GO
        else:
            decision = GateDecision.REVISE

        literature_ids = tuple(
            dict.fromkeys(significance_ids + candidate.novelty_evidence_ids)
        )
        literature_items = index.get(literature_ids)
        literature_status = (
            EvidenceStatus.VERIFIED
            if literature_ids
            and len(literature_items) == len(literature_ids)
            and all(item.status == EvidenceStatus.VERIFIED for item in literature_items)
            else EvidenceStatus.INSUFFICIENT
        )
        # Feasibility evidence describes executability, not completed results.
        # Only explicit experiment records can move this later-stage status.
        experiment_ids = index.verified_experiment_ids()
        experiment_status = EvidenceStatus.VERIFIED if experiment_ids else EvidenceStatus.PENDING
        return ValueGateDecision(
            problem_statement=candidate.problem_statement,
            significance=significance,
            novelty=novelty,
            technical_feasibility=feasibility,
            expected_contribution=candidate.expected_contribution,
            reviewer_objections=tuple(objections),
            literature={"status": literature_status, "evidence_ids": literature_ids},
            experiment={"status": experiment_status, "evidence_ids": experiment_ids},
            decision=decision,
        )
