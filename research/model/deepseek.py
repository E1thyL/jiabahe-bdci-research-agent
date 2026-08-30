"""Official DeepSeek V4 Flash client boundary; no request is made at import time."""

from __future__ import annotations

from dataclasses import dataclass
import json
import os
import time
from typing import Any, Callable
from urllib.request import Request, urlopen

from ..usage import MeasurementStatus, UsageSink, make_phase_usage_record


@dataclass(frozen=True)
class DeepSeekResponse:
    text: str
    input_tokens: int | None = None
    output_tokens: int | None = None
    total_tokens: int | None = None


class DeepSeekV4FlashClient:
    """Minimal OpenAI-compatible client for the official DeepSeek endpoint."""

    def __init__(self, *, endpoint: str | None = None, api_key: str | None = None,
                 model: str | None = None, timeout: float = 30.0, max_retries: int = 1,
                 request_fn: Callable[[str, dict[str, str], bytes, float], bytes] | None = None,
                 usage_sink: UsageSink | None = None, research_run_id: str | None = None,
                 artifact_path: str | None = None,
                 sleep_fn: Callable[[float], None] = time.sleep) -> None:
        self.endpoint = endpoint or os.environ.get("DEEPSEEK_API_ENDPOINT", "")
        self.api_key = api_key if api_key is not None else os.environ.get("DEEPSEEK_API_KEY", "")
        self.model = model or os.environ.get("DEEPSEEK_MODEL", "deepseek-v4-flash")
        self.timeout, self.max_retries = timeout, max_retries
        if not self.model.strip() or timeout <= 0 or max_retries < 0:
            raise ValueError("model, timeout, and retry settings are invalid")
        self._request = request_fn or _request
        self._sleep = sleep_fn
        self._usage_sink, self._run_id, self._artifact_path = usage_sink, research_run_id, artifact_path

    def generate(self, prompt: str, **kwargs: Any) -> str:
        if not self.endpoint.strip() or not self.api_key.strip():
            raise ValueError("DEEPSEEK_API_ENDPOINT and DEEPSEEK_API_KEY are required")
        usage_phase = kwargs.pop("_usage_phase", "value_gate")
        body = json.dumps({"model": self.model, "messages": [{"role": "user", "content": prompt}], **kwargs}).encode()
        started = time.monotonic()
        last_error: Exception | None = None
        for attempt in range(self.max_retries + 1):
            try:
                payload = json.loads(self._request(self.endpoint, {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}, body, self.timeout))
                response = _parse_response(payload)
                self._record_usage(response, int((time.monotonic() - started) * 1000), attempt, usage_phase)
                return response.text
            except (OSError, TimeoutError, ValueError, json.JSONDecodeError) as exc:
                last_error = exc
                if attempt == self.max_retries:
                    break
                self._sleep(0.1 * (2 ** attempt))
        self._record_failed_usage(int((time.monotonic() - started) * 1000), attempt, usage_phase)
        raise RuntimeError(f"DeepSeek request failed: {last_error}") from last_error

    def _record_usage(self, response: DeepSeekResponse, wall_time_ms: int, retries: int, phase: str) -> None:
        if self._usage_sink is None or not self._run_id:
            return
        values = {"input_tokens": response.input_tokens, "output_tokens": response.output_tokens,
                  "tool_calls": 0, "retry_count": retries, "wall_time_ms": wall_time_ms,
                  "reviewer_calls": 0, "request_count": retries + 1}
        status = MeasurementStatus.OBSERVED if response.input_tokens is not None and response.output_tokens is not None else MeasurementStatus.ESTIMATED
        self._usage_sink.record(make_phase_usage_record(phase=phase, research_run_id=self._run_id,
            artifact_path=self._artifact_path, model=self.model, measurement_status=status, **values))

    def _record_failed_usage(self, wall_time_ms: int, retries: int, phase: str) -> None:
        if self._usage_sink is None or not self._run_id:
            return
        self._usage_sink.record(make_phase_usage_record(
            phase=phase, research_run_id=self._run_id, artifact_path=self._artifact_path,
            model=self.model, measurement_status="pending", retry_count=retries,
            wall_time_ms=wall_time_ms, request_count=retries + 1,
        ))


def _request(endpoint: str, headers: dict[str, str], body: bytes, timeout: float) -> bytes:
    request = Request(endpoint, data=body, headers=headers, method="POST")
    with urlopen(request, timeout=timeout) as response:
        return response.read()


def _parse_response(payload: Any) -> DeepSeekResponse:
    if not isinstance(payload, dict) or not isinstance(payload.get("choices"), list) or not payload["choices"]:
        raise ValueError("DeepSeek response lacks choices")
    message = payload["choices"][0].get("message", {})
    text = message.get("content") if isinstance(message, dict) else None
    if not isinstance(text, str):
        raise ValueError("DeepSeek response lacks message content")
    usage = payload.get("usage") or {}
    return DeepSeekResponse(text, usage.get("prompt_tokens"), usage.get("completion_tokens"), usage.get("total_tokens"))
