from __future__ import annotations

import json

import pytest

from research.literature import (
    LiteratureSearchStatus,
    OpenAlexLiteratureSource,
)
from research.value_gate import (
    AdapterEvidenceCollector,
    CandidateProblem,
)


def _candidate() -> CandidateProblem:
    return CandidateProblem(problem_statement="context compression", topic="context_engineering")


def _work(**overrides) -> dict:
    work = {
        "id": "https://openalex.org/W1",
        "doi": "https://doi.org/10.1000/example",
        "title": "Evidence Preserving Context Compression",
        "publication_year": 2025,
        "authorships": [{"author": {"display_name": "A Researcher"}}],
        "primary_location": {
            "landing_page_url": "https://example.org/paper-1",
            "source": {"display_name": "Fixture Journal"},
        },
        "abstract_inverted_index": {"Evidence": [0], "matters": [1], "here": [2]},
    }
    work.update(overrides)
    return work


def _transport(payload: dict, calls: list[str] | None = None, status: int = 200):
    body = json.dumps(payload).encode()

    def request(url: str, timeout: float) -> tuple[int, bytes]:
        if calls is not None:
            calls.append(url)
        assert timeout == 2.0
        return status, body

    return request


def _source(tmp_path, request_fn, **kwargs) -> OpenAlexLiteratureSource:
    return OpenAlexLiteratureSource(
        cache_dir=tmp_path / "cache",
        research_run_id="research-001",
        timeout=2.0,
        request_fn=request_fn,
        sleep_fn=lambda _seconds: None,
        **kwargs,
    )


def test_openalex_normalizes_response_and_preserves_snapshot(tmp_path) -> None:
    source = _source(tmp_path, _transport({"results": [_work()]}))

    result = source.search(_candidate(), {"query": "fixture query"})
    bundle = result.to_evidence_bundle()

    assert result.status == LiteratureSearchStatus.SUCCESS
    assert result.query == "fixture query"
    assert result.raw_response["results"][0]["id"] == "https://openalex.org/W1"
    assert "research-001" in result.artifact_path
    assert bundle.items[0].source_uri == "https://example.org/paper-1"
    assert bundle.items[0].excerpt == "Evidence matters here"


def test_openalex_query_config_and_cache_are_deterministic(tmp_path) -> None:
    calls: list[str] = []
    source = _source(tmp_path, _transport({"results": [_work()]}, calls))

    first = source.search(_candidate(), {"query": "configured query"})
    second = source.search(_candidate(), {"query": "configured query"})

    assert len(calls) == 1
    assert "search=configured+query" in calls[0]
    assert first.to_evidence_bundle().items[0].source_hash == second.to_evidence_bundle().items[0].source_hash
    assert first.to_evidence_bundle().items[0].evidence_id == second.to_evidence_bundle().items[0].evidence_id


@pytest.mark.parametrize("status", [429, 500])
def test_openalex_retries_http_errors_then_fails(tmp_path, status: int) -> None:
    calls: list[str] = []
    source = _source(tmp_path, _transport({"error": "unavailable"}, calls, status), max_retries=2)

    result = source.search(_candidate())

    assert result.status == LiteratureSearchStatus.FAILED
    assert result.failure_reason == f"OpenAlex HTTP {status}"
    assert len(calls) == 3
    assert result.to_evidence_bundle().items == ()


def test_openalex_timeout_is_failed(tmp_path) -> None:
    def request(_url: str, _timeout: float) -> tuple[int, bytes]:
        raise TimeoutError("timed out")

    result = _source(tmp_path, request, max_retries=1).search(_candidate())

    assert result.status == LiteratureSearchStatus.FAILED
    assert "timed out" in result.failure_reason


@pytest.mark.parametrize("payload", [{"bad": True}, b"not-json"])
def test_openalex_malformed_json_or_shape_is_failed(tmp_path, payload) -> None:
    body = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
    result = _source(tmp_path, lambda _url, _timeout: (200, body)).search(_candidate())

    assert result.status == LiteratureSearchStatus.FAILED
    assert result.to_evidence_bundle().items == ()


def test_openalex_pagination_is_bounded(tmp_path) -> None:
    calls: list[str] = []
    payload = {"results": [_work() for _ in range(2)]}
    source = _source(tmp_path, _transport(payload, calls), max_pages=2, max_retries=0)

    result = source.search(_candidate(), {"per_page": 2})

    assert result.status == LiteratureSearchStatus.SUCCESS
    assert len(calls) == 2
    assert "page=2" in calls[1]


@pytest.mark.parametrize("field", ["primary_location", "abstract_inverted_index"])
def test_openalex_incomplete_record_becomes_partial(tmp_path, field: str) -> None:
    raw = _work(**{field: None})
    if field == "primary_location":
        raw.pop("doi")
        raw.pop("id")
    result = _source(tmp_path, _transport({"results": [raw]})).search(_candidate())

    assert result.status == LiteratureSearchStatus.PARTIAL
    assert result.to_evidence_bundle().items == ()


def test_openalex_empty_result_is_not_no_go(tmp_path) -> None:
    result = _source(tmp_path, _transport({"results": []})).search(_candidate())

    assert result.status == LiteratureSearchStatus.EMPTY
    assert result.failure_reason is None
    assert result.to_evidence_bundle().items == ()


def test_openalex_adapter_feeds_evidence_collector(tmp_path) -> None:
    source = _source(tmp_path, _transport({"results": [_work()]}))
    bundle = AdapterEvidenceCollector(source).collect(_candidate())

    assert len(bundle.items) == 1
    assert bundle.items[0].verification_status.value == "verified"
