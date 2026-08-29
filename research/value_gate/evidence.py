"""Offline evidence collection protocol and evidence indexing."""

from typing import Protocol

from .schema import CandidateProblem, EvidenceBundle, EvidenceItem, EvidenceStatus


class EvidenceCollector(Protocol):
    """Replaceable evidence source; implementations must remain offline-safe."""

    def collect(self, candidate: CandidateProblem) -> EvidenceBundle:
        ...


class FixtureEvidenceCollector:
    """Deterministic collector used by tests and local development."""

    def __init__(self, bundle: EvidenceBundle) -> None:
        self._bundle = bundle

    def collect(self, candidate: CandidateProblem) -> EvidenceBundle:
        del candidate
        return self._bundle


class EvidenceIndex:
    """Resolve evidence IDs without performing search or network I/O."""

    def __init__(self, bundle: EvidenceBundle | tuple[EvidenceItem, ...] = ()) -> None:
        if isinstance(bundle, EvidenceBundle):
            items = bundle.items
        else:
            items = EvidenceBundle(bundle).items
        self._items = {item.evidence_id: item for item in items}

    def get(self, evidence_ids: tuple[str, ...]) -> tuple[EvidenceItem, ...]:
        return tuple(
            self._items[evidence_id]
            for evidence_id in evidence_ids
            if evidence_id in self._items
        )

    @property
    def ids(self) -> set[str]:
        return set(self._items)

    def has_verified_literature(self, evidence_ids: tuple[str, ...]) -> bool:
        items = self.get(evidence_ids)
        return len(items) == len(evidence_ids) and any(
            item.kind == "literature" and item.status == EvidenceStatus.VERIFIED
            for item in items
        )

    def verified_experiment_ids(self) -> tuple[str, ...]:
        return tuple(
            item.evidence_id
            for item in self._items.values()
            if item.kind == "experiment" and item.status == EvidenceStatus.VERIFIED
        )
