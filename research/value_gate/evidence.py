"""Offline evidence collection protocol and evidence indexing."""

from typing import Any, Protocol

from ..usage import (
    ResearchUsageRecord,
    UsageSink,
    emit_usage,
    make_phase_usage_record,
)
from .schema import CandidateProblem, EvidenceBundle, EvidenceItem, EvidenceStatus
from ..literature.protocol import LiteratureSourceAdapter


class EvidenceCollector(Protocol):
    """Replaceable evidence source; implementations must remain offline-safe."""

    def collect(
        self,
        candidate: CandidateProblem,
        *,
        topic_config: dict[str, Any] | None = None,
        usage_sink: UsageSink | None = None,
        usage_record: ResearchUsageRecord | None = None,
        research_run_id: str | None = None,
        artifact_path: str | None = None,
        model: str = "",
    ) -> EvidenceBundle:
        ...


class FixtureEvidenceCollector:
    """Deterministic collector used by tests and local development."""

    def __init__(self, bundle: EvidenceBundle) -> None:
        self._bundle = bundle

    def collect(
        self,
        candidate: CandidateProblem,
        *,
        topic_config: dict[str, Any] | None = None,
        usage_sink: UsageSink | None = None,
        usage_record: ResearchUsageRecord | None = None,
        research_run_id: str | None = None,
        artifact_path: str | None = None,
        model: str = "",
    ) -> EvidenceBundle:
        del candidate, topic_config
        if usage_sink is not None:
            record = usage_record or make_phase_usage_record(
                phase="literature",
                research_run_id=research_run_id or "",
                artifact_path=artifact_path,
                model=model,
            )
            if record.phase.value != "literature":
                raise ValueError("EvidenceCollector usage record must use literature phase")
            emit_usage(usage_sink, record)
        return self._bundle


class AdapterEvidenceCollector:
    """Collect evidence from one injected literature adapter."""

    def __init__(self, adapter: LiteratureSourceAdapter) -> None:
        self._adapter = adapter

    def collect(
        self,
        candidate: CandidateProblem,
        *,
        topic_config: dict[str, Any] | None = None,
        usage_sink: UsageSink | None = None,
        usage_record: ResearchUsageRecord | None = None,
        research_run_id: str | None = None,
        artifact_path: str | None = None,
        model: str = "",
    ) -> EvidenceBundle:
        result = self._adapter.search(candidate, topic_config)
        bundle = result.to_evidence_bundle()
        if usage_sink is not None:
            record = usage_record or make_phase_usage_record(
                phase="literature",
                research_run_id=research_run_id or "",
                artifact_path=artifact_path,
                model=model,
            )
            if record.phase.value != "literature":
                raise ValueError("EvidenceCollector usage record must use literature phase")
            emit_usage(usage_sink, record)
        return bundle


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
