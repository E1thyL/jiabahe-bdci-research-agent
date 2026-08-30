"""Controlled candidate pilot entry point.

This script never persists the API key or the raw model response. Use
``--dry-run`` to validate configuration without making any network call.
"""

from __future__ import annotations

import argparse
from dataclasses import replace
import json
import os
from pathlib import Path
import sys
from typing import Any, Callable

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from research.literature import OpenAlexLiteratureSource, ReplayLiteratureSource, LiteratureQualityFilter, NoveltyGapBuilder  # noqa: E402
from research.literature.router import LiteratureRouter  # noqa: E402
from research.model.deepseek import DeepSeekV4FlashClient  # noqa: E402
from research.runtime_config import ResearchRuntimeConfig  # noqa: E402
from research.usage import UsageSink  # noqa: E402
from research.value_gate.schema import CandidateProblem  # noqa: E402
from research.value_gate.gate import ResearchValueGate  # noqa: E402


TOPICS = ("context_engineering", "memory_engine", "self_evolution")
FORBIDDEN = ("provenance-aware memory", "evidence-preserving context compaction", "review-gated reversible Skill evolution", "checkpoint", "trace", "replay recovery")


def validate_configuration(environ: dict[str, str] | None = None) -> dict[str, str]:
    values = os.environ if environ is None else environ
    required = ("DEEPSEEK_API_ENDPOINT", "DEEPSEEK_API_KEY", "DEEPSEEK_MODEL")
    missing = [name for name in required if not values.get(name, "").strip()]
    if missing:
        raise RuntimeError("missing DeepSeek configuration: " + ", ".join(missing))
    return {name: values[name] for name in required}


def bounded_topics(max_candidates: int) -> tuple[str, ...]:
    if max_candidates < 1:
        raise ValueError("max-candidates must be positive")
    return TOPICS[: min(max_candidates, len(TOPICS))]


def candidate_prompt(topic: str) -> str:
    banned = "; ".join(FORBIDDEN)
    return (
        f"Generate one structured research candidate for the Agent topic {topic}. "
        "Return JSON only with research_object, problem_statement, hypothesis, "
        "single_mechanism, closest_prior_work_risk, required_baselines, "
        "required_metrics, dataset_task, resource_budget. "
        f"Do not reuse these rejected problem formulations: {banned}."
    )


def parse_candidate(topic: str, value: str) -> CandidateProblem:
    try:
        data = json.loads(value)
    except json.JSONDecodeError as exc:
        raise ValueError(f"candidate response is not valid JSON for {topic}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"candidate response must be an object for {topic}")
    def text(name: str) -> str:
        item = data.get(name, "")
        return item if isinstance(item, str) else str(item)
    def seq(name: str) -> tuple[str, ...]:
        item = data.get(name, ())
        if isinstance(item, str):
            return (item,) if item else ()
        return tuple(str(value) for value in item) if isinstance(item, (list, tuple)) else ()
    return CandidateProblem(
        topic=topic, research_object=text("research_object"), problem_statement=text("problem_statement"),
        hypothesis=text("hypothesis"), expected_contribution=(text("single_mechanism"),),
        baselines=seq("required_baselines"), metrics=seq("required_metrics"), datasets=seq("dataset_task"),
    )


def run_pilot(*, run_id: str, max_candidates: int, client: Any, router: LiteratureRouter,
              artifact_dir: Path, secret: str, usage_sink: UsageSink | None = None,
              write_artifact: bool = True) -> dict[str, Any]:
    results = []
    for topic in bounded_topics(max_candidates):
        candidate = parse_candidate(topic, _generate_candidate(client, candidate_prompt(topic)))
        search = router.search(
            candidate,
            {"query": candidate.problem_statement},
            usage_sink=usage_sink,
            research_run_id=run_id,
            artifact_path=f"artifacts/{run_id}/literature.json",
        )
        bundle = search.to_evidence_bundle()
        evidence_ids = tuple(sorted(bundle.ids()))
        candidate = replace(candidate, significance_evidence_ids=evidence_ids,
                            closest_prior_work=evidence_ids, novelty_evidence_ids=evidence_ids,
                            gap=candidate.hypothesis, difference=candidate.expected_contribution[0] if candidate.expected_contribution else "",
                            feasibility_evidence_ids=evidence_ids)
        quality = LiteratureQualityFilter().evaluate(candidate, bundle, search)
        novelty = NoveltyGapBuilder().build(candidate, bundle, quality)
        decision = ResearchValueGate().evaluate(candidate, bundle)
        results.append({"topic": topic, "candidate": _safe(candidate.__dict__, secret), "search_status": search.status.value,
                        "evidence_ids": list(evidence_ids), "source": search.source_name,
                        "artifact_path": search.artifact_path, "quality": _safe(quality.to_dict(), secret),
                        "novelty_gap": _safe(novelty.to_dict(), secret),
                        "mechanical_gate_decision": decision.decision.value,
                        "scientific_review_decision": "revise" if novelty.status != "supported" else decision.decision.value,
                        "status": novelty.status, "reason": list(decision.reviewer_objections) + list(novelty.unsupported_claims),
                        "closest_prior_work_ids": list(novelty.closest_prior_work_ids),
                        "supported_gap": novelty.supported_gap, "candidate_difference": novelty.candidate_difference,
                        "baseline_plan": list(candidate.baselines), "metric_plan": list(candidate.metrics)})
    usage = tuple(getattr(usage_sink, "records", ()))
    report = {"research_run_id": run_id, "candidate_count": len(results), "method_design": False,
              "drafting": False, "stanford_reviewer": False, "usage": [record.to_dict() for record in usage],
              "candidates": results}
    if write_artifact:
        artifact_dir.mkdir(parents=True, exist_ok=True)
        (artifact_dir / "candidate_pilot.json").write_text(json.dumps(_safe(report, secret), ensure_ascii=False, indent=2), encoding="utf-8")
    return report


def _safe(value: Any, secret: str) -> Any:
    if isinstance(value, str):
        return value.replace(secret, "[REDACTED]") if secret else value
    if isinstance(value, dict):
        return {key: _safe(item, secret) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [_safe(item, secret) for item in value]
    return value


class _UsageCollector:
    def __init__(self) -> None:
        self.records = []

    def record(self, record: Any) -> None:
        self.records.append(record)


def _generate_candidate(client: Any, prompt: str) -> str:
    """Use explicit ideation phase while tolerating legacy test clients."""
    try:
        import inspect
        signature = inspect.signature(client.generate)
        accepts_kwargs = any(parameter.kind == inspect.Parameter.VAR_KEYWORD
                             for parameter in signature.parameters.values())
        if accepts_kwargs or "_usage_phase" in signature.parameters:
            return client.generate(prompt, _usage_phase="ideation")
    except (TypeError, ValueError):
        return client.generate(prompt, _usage_phase="ideation")
    return client.generate(prompt)


def _make_client(factory: Callable[..., Any], config: dict[str, str], *, usage_sink: UsageSink,
                 run_id: str, artifact_path: str) -> Any:
    kwargs = {
        "endpoint": config["DEEPSEEK_API_ENDPOINT"],
        "api_key": config["DEEPSEEK_API_KEY"],
        "model": config["DEEPSEEK_MODEL"],
        "usage_sink": usage_sink,
        "research_run_id": run_id,
        "artifact_path": artifact_path,
    }
    try:
        import inspect
        signature = inspect.signature(factory)
        accepts_kwargs = any(parameter.kind == inspect.Parameter.VAR_KEYWORD
                             for parameter in signature.parameters.values())
        if accepts_kwargs or all(name in signature.parameters for name in kwargs):
            return factory(**kwargs)
    except (TypeError, ValueError):
        pass
    # Preserve factories that predate usage wiring while keeping the default
    # client fully instrumented above.
    return factory(endpoint=kwargs["endpoint"], api_key=kwargs["api_key"], model=kwargs["model"])


def main(argv: list[str] | None = None, *, environ: dict[str, str] | None = None,
         client_factory: Callable[..., Any] = DeepSeekV4FlashClient) -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--max-candidates", type=int, default=3)
    parser.add_argument("--run-id", default="controlled-pilot")
    args = parser.parse_args(argv)
    try:
        config = validate_configuration(environ)
        topics = bounded_topics(args.max_candidates)
        if args.dry_run:
            print(json.dumps({"status": "ready", "mode": "dry-run", "model": config["DEEPSEEK_MODEL"], "candidate_limit": len(topics), "network_calls": 0}))
            return 0
        runtime = ResearchRuntimeConfig.from_env(environ)
        usage_sink = _UsageCollector()
        artifact_path = f"artifacts/{args.run_id}/candidate_pilot.json"
        client = _make_client(client_factory, config, usage_sink=usage_sink,
                              run_id=args.run_id, artifact_path=artifact_path)
        online = OpenAlexLiteratureSource(cache_dir=ROOT / ".pilot-cache", research_run_id=args.run_id, max_pages=1, max_retries=1)
        offline = ReplayLiteratureSource({})
        report = run_pilot(run_id=args.run_id, max_candidates=len(topics), client=client,
                           router=LiteratureRouter(runtime, offline=offline, online=online),
                           artifact_dir=ROOT / ".pilot-cache" / args.run_id, secret=config["DEEPSEEK_API_KEY"],
                           usage_sink=usage_sink)
        print(json.dumps({"status": "completed", "research_run_id": report["research_run_id"], "candidate_count": report["candidate_count"]}))
        return 0
    except Exception as exc:
        secret_value = (environ if environ is not None else os.environ).get("DEEPSEEK_API_KEY", "")
        message = str(exc).replace(secret_value, "[REDACTED]") if secret_value else str(exc)
        print(f"candidate pilot failed: {message}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
