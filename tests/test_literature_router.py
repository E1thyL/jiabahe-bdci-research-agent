from __future__ import annotations

import pytest

from research.literature import LiteratureRecord, LiteratureSearchStatus, ReplayLiteratureSource
from research.literature.router import LiteratureRouter
from research.runtime_config import LiteratureMode, ResearchRuntimeConfig
from research.value_gate import CandidateProblem


def candidate() -> CandidateProblem:
    return CandidateProblem(problem_statement="q", research_object="agent")


def record() -> LiteratureRecord:
    return LiteratureRecord("https://example.org/p", "Paper", (), 2025, "Venue", "Abstract", "prior_work")


class FakeOnline:
    _source_name = "openalex"
    API_URL = "https://api.openalex.org/works"

    def __init__(self, result=None, error=None):
        self.result, self.error, self.calls = result, error, 0

    def search(self, candidate, topic_config=None):
        self.calls += 1
        if self.error:
            raise self.error
        return self.result


def offline_source():
    return ReplayLiteratureSource({"q": (record(),)})


def test_offline_never_calls_online():
    online = FakeOnline()
    router = LiteratureRouter(ResearchRuntimeConfig(LiteratureMode.OFFLINE), offline=offline_source(), online=online)
    assert router.search(candidate()).status == LiteratureSearchStatus.SUCCESS
    assert online.calls == 0


def test_online_allowlist_accepts_openalex_only():
    result = offline_source().search(candidate())
    online = FakeOnline(result)
    router = LiteratureRouter(ResearchRuntimeConfig("online_allowlist"), offline=offline_source(), online=online)
    assert router.search(candidate()).records == result.records
    assert online.calls == 1


def test_unknown_online_endpoint_is_rejected():
    class Bad(FakeOnline):
        API_URL = "https://example.org/search"
    with pytest.raises(ValueError, match="allowlisted"):
        LiteratureRouter(ResearchRuntimeConfig("auto"), offline=offline_source(), online=Bad())


def test_auto_falls_back_after_online_failure():
    online = FakeOnline(error=TimeoutError("offline"))
    router = LiteratureRouter(ResearchRuntimeConfig("auto"), offline=offline_source(), online=online)
    assert router.search(candidate()).records[0].title == "Paper"


def test_auto_falls_back_on_failed_result_and_records_pending_usage():
    failed = offline_source().search(candidate(), {"query": "missing"})
    online = FakeOnline(failed)
    received = []
    router = LiteratureRouter(ResearchRuntimeConfig("auto"), offline=offline_source(), online=online)

    class Sink:
        def record(self, item):
            received.append(item)

    result = router.search(candidate(), usage_sink=Sink(), research_run_id="run-1")
    assert result.status == LiteratureSearchStatus.EMPTY
    assert received[0].measurement_status.value == "pending"
    assert received[0].input_tokens is None


def test_online_usage_with_explicit_measurement_is_estimated():
    online = FakeOnline(offline_source().search(candidate()))
    received = []
    router = LiteratureRouter(ResearchRuntimeConfig("online_allowlist"), offline=offline_source(), online=online)

    class Sink:
        def record(self, item):
            received.append(item)

    router.search(candidate(), usage_sink=Sink(), research_run_id="run-2", usage_measurement={"tool_calls": 1, "wall_time_ms": 12})
    assert received[0].measurement_status.value == "estimated"
    assert received[0].tool_calls == 1
    assert received[0].output_tokens is None


def test_runtime_config_from_env_defaults_to_auto():
    config = ResearchRuntimeConfig.from_env({"LITERATURE_MODE": "offline", "LITERATURE_ONLINE_SOURCES": "openalex"})
    assert config.literature_mode == LiteratureMode.OFFLINE
    assert config.online_sources == ("openalex",)
