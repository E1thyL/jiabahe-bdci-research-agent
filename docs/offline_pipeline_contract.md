# Offline pipeline contract

The `codex/experiment-evidence` branch supports deterministic, offline-only
execution. `ExperimentExecutor` consumes a fixture (or a deterministic callable)
and labels provenance as `offline://fixture`; it does not call a model or
network and its record remains `verification_status=pending` until an explicitly
verified result is supplied. A failed fixture produces a `failed` record and
cannot become verified.

`ResultAnalysisStage` preserves the historical `pending` boundary when no
records are supplied. With explicit verified records it emits descriptive
metric data and a `ready` analysis status, without making significance claims.
`ClaimMap.validate` rejects unknown or missing evidence, duplicate claim IDs,
missing citations, and evidence whose support level is below the claim's
minimum; metadata/abstract evidence cannot support a technical-difference
claim.

`check_drafting_readiness` is a model- and reviewer-free G3 check. It returns
`ready` only when verified experiment data, a ready analysis, a complete claim
map, a non-`no_go` value gate, and usage records are present. Otherwise it
returns `blocked` with named missing conditions. Real experiment execution,
model usage, literature retrieval, and Stanford Reviewer review remain outside
this offline contract.
