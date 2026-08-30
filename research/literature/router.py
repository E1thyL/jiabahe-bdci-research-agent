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
            self._validate_online_adapter(online, config.online_sources)

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
            result = self.offline.search(candidate, topic_config)
            if usage_sink is not None and research_run_id:
                self._emit_usage(usage_sink, research_run_id, artifact_path, None)
            return result
        if self.online is None:
            if mode == LiteratureMode.ONLINE_ALLOWLIST:
                result = LiteratureSearchResult(candidate.problem_statement, "", "router", status=LiteratureSearchStatus.FAILED, failure_reason="no allowlisted online adapter configured")
            else:
                result = self.offline.search(candidate, topic_config)
            if usage_sink is not None and research_run_id:
                self._emit_usage(usage_sink, research_run_id, artifact_path, None)
            return result
        try:
            result = self.online.search(candidate, topic_config)
        except Exception as exc:
            if mode == LiteratureMode.ONLINE_ALLOWLIST:
                result = LiteratureSearchResult(candidate.problem_statement, "", "router", status=LiteratureSearchStatus.FAILED, failure_reason=str(exc))
            else:
                result = self.offline.search(candidate, topic_config)
        if usage_sink is not None and research_run_id:
            measured = getattr(self.online, "usage_measurement", None)
            if callable(measured):
                measured = measured()
            if measured is None:
                measured = usage_measurement
            elif usage_measurement:
                measured = {**measured, **usage_measurement}
            actual_artifact_path = self._artifact_path_for_usage(result, research_run_id) or artifact_path
            self._emit_usage(usage_sink, research_run_id, actual_artifact_path, measured)
        if mode == LiteratureMode.AUTO and result.status == LiteratureSearchStatus.FAILED:
            return self.offline.search(candidate, topic_config)
        return result

    @staticmethod
    def _validate_online_adapter(adapter: LiteratureSourceAdapter, allowed_sources: tuple[str, ...]) -> None:
        source = str(getattr(adapter, "_source_name", getattr(adapter, "source_name", ""))).lower()
        if source not in allowed_sources:
            raise ValueError(f"online adapter is not allowlisted: {source or '<unknown>'}")
        endpoint = getattr(adapter, "API_URL", getattr(adapter, "api_url", ""))
        host = urlparse(str(endpoint)).netloc.lower()
        expected = {"openalex": "api.openalex.org", "arxiv": "export.arxiv.org"}[source]
        if host and host != expected:
            raise ValueError(f"online adapter endpoint is not allowlisted: {host}")

    @staticmethod
    def _artifact_path_for_usage(result: LiteratureSearchResult, run_id: str) -> str | None:
        from pathlib import PurePosixPath
        path = result.artifact_path
        if not path:
            return None
        normalized = path.replace("\\", "/")
        parsed = PurePosixPath(normalized)
        if parsed.is_absolute() or ".." in parsed.parts or run_id not in parsed.parts:
            return None
        return parsed.as_posix()

    @staticmethod
    def _emit_usage(sink: UsageSink, run_id: str, artifact_path: str | None, measurement: dict[str, int | None] | None) -> None:
        values = measurement or {}
        status = MeasurementStatus.ESTIMATED if measurement is not None else MeasurementStatus.PENDING
        path = artifact_path or f"artifacts/{run_id}/literature-pending.json"
        sink.record(make_phase_usage_record(
            phase="literature", research_run_id=run_id, artifact_path=path,
            model="", measurement_status=status, **values,
        ))
