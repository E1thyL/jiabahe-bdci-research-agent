"""Topic-specific review prompts and thresholds."""

TOPIC_POLICIES = {
    "context_engineering": {
        "criteria": (
            "key evidence retention after context compression",
            "multi-agent information contamination",
            "quality gain relative to token cost",
        ),
        "required_baselines": ("full_context", "summary_only"),
        "required_metrics": ("task_quality", "token_cost"),
    },
    "memory_engine": {
        "criteria": (
            "long-horizon task improvement",
            "incorrect-memory eviction",
            "comparison with vector retrieval and summary memory",
        ),
        "required_baselines": ("vector_retrieval", "summary_memory"),
        "required_metrics": ("long_horizon_success", "memory_precision"),
    },
    "self_evolution": {
        "criteria": (
            "measurable capability improvement",
            "incorrect Skill propagation risk",
            "testability, reviewability, and rollback safety",
        ),
        "required_baselines": ("static_skill_set", "no_evolution"),
        "required_metrics": ("capability_gain", "regression_rate"),
    },
}


def topic_policy(topic: str) -> dict:
    """Return a copy of the configured policy for *topic*."""
    if topic not in TOPIC_POLICIES:
        raise ValueError(f"unsupported research topic: {topic}")
    return dict(TOPIC_POLICIES[topic])
