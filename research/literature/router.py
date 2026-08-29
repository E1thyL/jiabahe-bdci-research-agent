"""Allowlisted online literature routing with offline fallback."""

from __future__ import annotations

from typing import Any
from urllib.parse import urlparse

from ..runtime_config import LiteratureMode, ResearchRuntimeConfig
from ..usage import MeasurementStatus, ResearchUsageRecord, UsageSink, make_phase_usage_record
from ..value_gate.schema import CandidateProblem
from .protocol import LiteratureSearchResult, LiteratureSearchStatus, LiteratureSourceAdapter


class LiteratureRouter:
    """Route searches without allowing arbitrary network adapters."""

    def __init__(
        self,
        config: ResearchRuntimeConfig,
        *,
        offline: LiteratureSourceAdapter,
        online: LiteratureSourceAdapter | None = None,
    ) -> None:
        self.config = config
        self.offline = offline
        self.online = online
        if online is not None:
            self._validate_online_adapter(online)

    def search(
        self,
        candidate: CandidateProblem,
        topic_config: dict[str, Any] | None = None,
        *,
        usage_sink: UsageSink | None = None,
        research_run_id: str | None = None,
        artifact_path: str | None = None,
        usage_measurement: dict[str, int | None] | None = None,
    ) -> LiteratureSearchResult:
        mode = self.config.literature_mode
        if mode == LiteratureMode.OFFLINE:
            return self.offline.search(candidate, topic_config)
        if self.online is None:
            if mode == LiteratureMode.ONLINE_ALLOWLIST:
                return LiteratureSearchResult(candidate.problem_statement, "", "router", status=LiteratureSearchStatus.FAILED, failure_reason="no allowlisted online adapter configured")
            return self.offline.search(candidate, topic_config)
        try:
            result = self.online.search(candidate, topic_config)
        except Exception as exc:
            if mode == LiteratureMode.ONLINE_ALLOWLIST:
                return LiteratureSearchResult(candidate.problem_statement, "", "router", status=LiteratureSearchStatus.FAILED, failure_reason=str(exc))
            result = self.offline.search(candidate, topic_config)
        if usage_sink is not None and research_run_id:
            self._emit_usage(usage_sink, research_run_id, artifact_path, usage_measurement)
        if mode == LiteratureMode.AUTO and result.status == LiteratureSearchStatus.FAILED:
            return self.offline.search(candidate, topic_config)
        return result

    @staticmethod
    def _validate_online_adapter(adapter: LiteratureSourceAdapter) -> None:
        source = str(getattr(adapter, "_source_name", getattr(adapter, "source_name", ""))).lower()
        if source not in {"openalex", "arxiv"}:
            raise ValueError(f"online adapter is not allowlisted: {source or '<unknown>'}")
        endpoint = getattr(adapter, "API_URL", getattr(adapter, "api_url", ""))
        host = urlparse(str(endpoint)).netloc.lower()
        expected = {"openalex": "api.openalex.org", "arxiv": "export.arxiv.org"}[source]
        if host and host != expected:
            raise ValueError(f"online adapter endpoint is not allowlisted: {host}")

    @staticmethod
    def _emit_usage(sink: UsageSink, run_id: str, artifact_path: str | None, measurement: dict[str, int | None] | None) -> None:
        values = measurement or {}
        status = MeasurementStatus.ESTIMATED if measurement is not None else MeasurementStatus.PENDING
        sink.record(make_phase_usage_record(
            phase="literature", research_run_id=run_id, artifact_path=artifact_path,
            model="", measurement_status=status, **values,
        ))
