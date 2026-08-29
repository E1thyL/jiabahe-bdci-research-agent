from __future__ import annotations

import json
from urllib.error import HTTPError

import pytest

from research.model.deepseek import DeepSeekV4FlashClient


class Sink:
    def __init__(self):
        self.records = []
    def record(self, record):
        self.records.append(record)


def payload(usage=None):
    result = {"choices": [{"message": {"content": "ok"}}]}
    if usage is not None:
        result["usage"] = usage
    return json.dumps(result).encode()


def client(request_fn, **kwargs):
    kwargs.setdefault("sleep_fn", lambda _: None)
    return DeepSeekV4FlashClient(
        endpoint="https://example.invalid/v1/chat/completions", api_key="test-secret",
        model="deepseek-v4-flash-test", request_fn=request_fn,
        **kwargs,
    )


def test_configuration_is_injected_from_environment(monkeypatch):
    monkeypatch.setenv("DEEPSEEK_API_ENDPOINT", "https://example.invalid/custom")
    monkeypatch.setenv("DEEPSEEK_API_KEY", "env-secret")
    monkeypatch.setenv("DEEPSEEK_MODEL", "deepseek-v4-flash-env")
    c = DeepSeekV4FlashClient(request_fn=lambda *_: payload())
    assert c.endpoint == "https://example.invalid/custom"
    assert c.api_key == "env-secret"
    assert c.model == "deepseek-v4-flash-env"


def test_fake_transport_verifies_request_shape_and_never_uses_network():
    calls = []
    def transport(endpoint, headers, body, timeout):
        calls.append((endpoint, headers, json.loads(body), timeout))
        assert endpoint == "https://example.invalid/v1/chat/completions"
        assert headers["Content-Type"] == "application/json"
        assert headers["Authorization"] == "Bearer test-secret"
        return payload()
    assert client(transport, timeout=7.5).generate("hello") == "ok"
    assert calls[0][2]["model"] == "deepseek-v4-flash-test"
    assert calls[0][2]["messages"] == [{"role": "user", "content": "hello"}]
    assert calls[0][3] == 7.5


def test_complete_usage_is_observed():
    sink = Sink()
    c = client(lambda *_: payload({"prompt_tokens": 100, "completion_tokens": 50, "total_tokens": 150}), usage_sink=sink, research_run_id="run-usage")
    assert c.generate("p", _usage_phase="literature") == "ok"
    record = sink.records[0]
    assert (record.input_tokens, record.output_tokens) == (100, 50)
    assert record.measurement_status.value == "observed"
    assert record.phase.value == "literature"


@pytest.mark.parametrize("usage", [None, {"prompt_tokens": 100}])
def test_missing_or_partial_usage_is_not_observed_zero(usage):
    sink = Sink()
    client(lambda *_: payload(usage), usage_sink=sink, research_run_id="run-partial").generate("p")
    record = sink.records[0]
    assert record.measurement_status.value == "estimated"
    assert record.input_tokens is None or record.output_tokens is None
    assert record.measurement_status.value != "observed" or record.input_tokens != 0


@pytest.mark.parametrize("code", [429, 500, 503])
def test_retryable_http_errors_retry_up_to_limit(code):
    calls, sleeps = [], []
    def transport(*_):
        calls.append(1)
        raise HTTPError("https://example.invalid", code, "failure", {}, None)
    with pytest.raises(RuntimeError, match="request failed"):
        client(transport, max_retries=2, sleep_fn=sleeps.append).generate("p")
    assert len(calls) == 3
    assert len(sleeps) == 2


def test_success_is_not_retried():
    calls = []
    assert client(lambda *_: (calls.append(1), payload())[1], max_retries=2).generate("p") == "ok"
    assert len(calls) == 1


def test_configuration_error_does_not_retry_or_expose_key():
    calls = []
    c = DeepSeekV4FlashClient(endpoint="https://example.invalid", api_key="super-secret", request_fn=lambda *_: calls.append(1))
    c.api_key = ""
    with pytest.raises(ValueError, match="API_ENDPOINT and DEEPSEEK_API_KEY") as exc:
        c.generate("p")
    assert not calls
    assert "super-secret" not in repr(c)
    assert "super-secret" not in str(exc.value)


def test_api_key_not_in_request_error_or_artifact():
    def transport(*_):
        raise TimeoutError("transport timeout")
    c = client(transport, max_retries=0, artifact_path="artifacts/run-safe/value_gate.json")
    with pytest.raises(RuntimeError) as exc:
        c.generate("do not include secret")
    serialized = c.endpoint + " " + str(exc.value)
    assert "test-secret" not in serialized
    assert "test-secret" not in c._artifact_path
