# Research Pipeline Contract

`ResearchPipelineRunner` is the minimum stage wiring for the research Agent. It is deliberately a skeleton: method, experiment, drafting and review artifacts are placeholders until a scientifically approved candidate exists.

```text
ideation
  -> literature (LiteratureRouter)
  -> value_gate (ResearchValueGate)
  -> method_design
  -> experiment_design
  -> drafting
  -> internal_review
  -> publication_review
```

Every artifact is a dictionary containing `research_run_id`. Literature results are converted through the existing `LiteratureSearchResult.to_evidence_bundle()` path, so the Gate can only reference evidence IDs present in that bundle. A `revise` or `no_go` Gate result returns before method design and drafting; it is never silently promoted to a paper.

The model boundary is `OfficialDeepSeekClient` / `DeepSeekV4FlashClient`. Endpoint, key and model are injected through configuration or environment variables. The implementation is not called at import time and tests use a fake client. Provider usage is recorded as `observed` only when both input and output token counts are returned. Otherwise the record remains `estimated` or `pending`, with unknown token fields set to `null`.

The pipeline accepts a `LiteratureRouter`, so offline tests use `ReplayLiteratureSource` and production wiring can select `offline`, `online_allowlist` or `auto`. No real network or model request is required for the offline path.
