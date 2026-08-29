from __future__ import annotations

import json

import pytest

from research.literature import LiteratureRecord, LiteratureSearchResult, ReplayLiteratureSource
from research.literature.router import LiteratureRouter
from research.runtime_config import ResearchRuntimeConfig
from research.value_gate.schema import CandidateProblem

from scripts.run_candidate_pilot import bounded_topics, main, parse_candidate, run_pilot, validate_configuration


ENV = {"DEEPSEEK_API_ENDPOINT": "https://example.invalid/v1/chat/completions", "DEEPSEEK_API_KEY": "test-secret", "DEEPSEEK_MODEL": "deepseek-v4-flash"}


def response():
    return json.dumps({"research_object": "agent evaluation", "problem_statement": "q", "hypothesis": "h", "single_mechanism": "mechanism", "closest_prior_work_risk": "risk", "required_baselines": ["b1", "b2"], "required_metrics": ["m1", "m2"], "dataset_task": ["task"], "resource_budget": "small"})


class FakeClient:
    model = "deepseek-v4-flash"
    def __init__(self, *args, **kwargs):
        self.calls = []
    def generate(self, prompt):
        self.calls.append(prompt)
        return response()


class CountingAdapter:
    def __init__(self):
        self.calls = 0
    def search(self, candidate, topic_config=None):
        self.calls += 1
        return LiteratureSearchResult(candidate.problem_statement, "q", "replay")


def test_complete_configuration_dry_run_passes_without_network(capsys):
    assert main(["--dry-run", "--max-candidates", "3"], environ=ENV) == 0
    output = capsys.readouterr().out
    assert '"network_calls": 0' in output


def test_missing_configuration_dry_run_fails_clearly(capsys):
    assert main(["--dry-run"], environ={}) == 2
    assert "missing DeepSeek configuration" in capsys.readouterr().err


def test_dry_run_does_not_construct_client_or_send_network():
    def forbidden(*args, **kwargs):
        raise AssertionError("network/client must not be constructed")
    assert main(["--dry-run"], environ=ENV, client_factory=forbidden) == 0


def test_candidate_limit_is_bounded():
    assert len(bounded_topics(99)) == 3
    with pytest.raises(ValueError):
        bounded_topics(0)


def test_each_candidate_searches_at_most_once():
    adapter = CountingAdapter()
    source = ReplayLiteratureSource({})
    router = LiteratureRouter(ResearchRuntimeConfig("offline"), offline=adapter)
    client = FakeClient()
    report = run_pilot(run_id="run-1", max_candidates=3, client=client, router=router, artifact_dir=__import__('pathlib').Path(".pilot-cache/test-run"), secret="test-secret", write_artifact=False)
    assert report["candidate_count"] == 3
    assert adapter.calls == 3
    assert len(client.calls) == 3


def test_key_is_not_in_report_or_error(capsys, tmp_path):
    adapter = CountingAdapter()
    router = LiteratureRouter(ResearchRuntimeConfig("offline"), offline=adapter)
    report = run_pilot(run_id="run-safe", max_candidates=1, client=FakeClient(), router=router, artifact_dir=tmp_path, secret="test-secret")
    serialized = json.dumps(report)
    assert "test-secret" not in serialized
    assert main(["--dry-run"], environ={"DEEPSEEK_API_KEY": "test-secret"}) == 2
    assert "test-secret" not in capsys.readouterr().err


def test_candidate_schema_contains_required_fields():
    candidate = parse_candidate("memory_engine", response())
    assert isinstance(candidate, CandidateProblem)
    assert candidate.topic == "memory_engine"
    assert candidate.baselines == ("b1", "b2")
