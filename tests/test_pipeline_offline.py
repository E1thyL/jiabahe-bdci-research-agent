from __future__ import annotations

import json

from research.literature import LiteratureRecord, ReplayLiteratureSource
from research.literature.router import LiteratureRouter
from research.model.deepseek import DeepSeekV4FlashClient
from research.pipeline import ResearchPipelineRunner
from research.runtime_config import ResearchRuntimeConfig
from research.usage import aggregate_usage
from research.value_gate import CandidateProblem


class Sink:
    def __init__(self):
        self.records = []
    def record(self, record):
        self.records.append(record)


class FakeClient:
    model = "fake-deepseek-v4-flash"
    def __init__(self):
        self.calls = []
    def generate(self, prompt, **kwargs):
        self.calls.append((prompt, kwargs))
        return "offline generated placeholder"


def item():
    return LiteratureRecord("https://example.org/paper", "Prior work", ("A",), 2025, "Conf", "Sourced abstract", "prior_work")


def candidate(evidence_id: str, *, complete: bool = True):
    values = dict(
        problem_statement="How can an agent preserve evidence?", research_object="research agent",
        hypothesis="Evidence constraints reduce unsupported claims", topic="context_engineering",
        significance_evidence_ids=(evidence_id,), closest_prior_work=(evidence_id,),
        novelty_evidence_ids=(evidence_id,), gap="prior work leaves a measurable gap",
        difference="a tested evidence constraint", datasets=("fixture tasks",),
        baselines=("baseline",), metrics=("unsupported claim rate",),
        feasibility_evidence_ids=(evidence_id,), expected_contribution=("protocol",),
    )
    if not complete:
        values["gap"] = ""
    return CandidateProblem(**values)


def runner(sink, client):
    source = ReplayLiteratureSource({"q": (item(),)})
    router = LiteratureRouter(ResearchRuntimeConfig("offline"), offline=source)
    return ResearchPipelineRunner(literature_router=router, model_client=client, usage_sink=sink)


def test_offline_pipeline_runs_through_review_with_run_scoped_artifacts():
    source = ReplayLiteratureSource({"q": (item(),)})
    evidence_id = source.search(candidate("unused"), {"query": "q"}).to_evidence_bundle().items[0].evidence_id
    sink, client = Sink(), FakeClient()
    result = runner(sink, client).run(candidate(evidence_id), research_run_id="research-001", topic_config={"query": "q"})

    assert result.status == "drafting_blocked"
    assert set(result.artifacts) == {"ideation", "literature", "value_gate", "method_design", "experiment_design", "experiment_execution", "result_analysis"}
    assert all(a["research_run_id"] == "research-001" for a in result.artifacts.values())
    assert len(client.calls) == 3
    assert result.artifacts["result_analysis"]["claim_map"] is None
    assert all(r.research_run_id == "research-001" for r in sink.records)


def test_revise_gate_does_not_enter_drafting():
    source = ReplayLiteratureSource({"q": (item(),)})
    evidence_id = source.search(candidate("unused"), {"query": "q"}).to_evidence_bundle().items[0].evidence_id
    result = runner(Sink(), FakeClient()).run(candidate(evidence_id, complete=False), research_run_id="research-002", topic_config={"query": "q"})

    assert result.status == "revise"
    assert "drafting" not in result.artifacts
    assert result.decision.decision.value == "revise"


def test_fake_client_usage_can_be_aggregated_without_observed_zero_tokens():
    sink, client = Sink(), FakeClient()
    source = ReplayLiteratureSource({"q": (item(),)})
    evidence_id = source.search(candidate("unused"), {"query": "q"}).to_evidence_bundle().items[0].evidence_id
    runner(sink, client).run(candidate(evidence_id), research_run_id="research-003", topic_config={"query": "q"})
    totals = aggregate_usage(sink.records)
    assert totals["total_input_tokens"] == 0
    assert all(r.measurement_status.value == "pending" for r in sink.records)
    assert all(r.input_tokens is None for r in sink.records)


def test_official_client_parses_usage_and_records_observed():
    payload = {"choices": [{"message": {"content": "answer"}}], "usage": {"prompt_tokens": 4, "completion_tokens": 3, "total_tokens": 7}}
    sink = Sink()
    def request(endpoint, headers, body, timeout):
        assert endpoint == "https://api.deepseek.example/v1/chat/completions"
        assert headers["Authorization"] == "Bearer secret"
        assert json.loads(body)["model"] == "deepseek-v4-flash"
        return json.dumps(payload).encode()
    client = DeepSeekV4FlashClient(endpoint="https://api.deepseek.example/v1/chat/completions", api_key="secret", model="deepseek-v4-flash", request_fn=request, usage_sink=sink, research_run_id="research-004")
    assert client.generate("prompt", _usage_phase="literature") == "answer"
    assert sink.records[0].measurement_status.value == "observed"
    assert sink.records[0].phase.value == "literature"
    assert sink.records[0].input_tokens == 4
