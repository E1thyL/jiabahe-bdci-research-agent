# Proposed Schema Implementation Checklist

This is an implementation review checklist for Codex, not a second overarching
contract. The scientific rules live in `docs/paper_quality_contract.md`; this file
turns the five items that document marks "(proposed)" into concrete, checkable
implementation requirements.

It does not implement code, does not change existing code, and does not schedule the
work. Type names, field names, and signatures below are indicative; the implementing
PR is the source of truth for exact shapes.

Code facts cited below are read from `main` at `991b2e5`:
`research/value_gate/schema.py`, `research/value_gate/evidence.py`,
`research/value_gate/gate.py`, and `research/usage.py`. Re-verify against the working
tree before implementing, because the checklist ages as the code changes.

The facts below are the pre-implementation baseline. After an item lands, its
status must be updated from "current gap" to "implemented" in the active design
documentation; do not use the historical baseline statements as a description of
the latest branch.

## How to read each item

Every item is stated on seven axes:

- Current code facts: what the code enforces today, cited to symbols.
- Proposed target: what the extension should add.
- Required contract properties: invariants the implementation must hold.
- Illegal states to reject: inputs that must be refused, not silently accepted.
- Serialization and backward compatibility: JSON shape and migration of existing data.
- Minimum test acceptance: the smallest test set that proves the item.
- Undecided implementation details: choices to settle before coding, not guessed here.

A property that is not yet enforced by code is stated as a target, never as a current
capability.

## 1. ScientificSupportLevel

Current code facts:

- `schema.py` has no support-level concept. `EvidenceItem.verification_status` is an
  `EvidenceStatus` (`verified` / `pending` / `insufficient`) describing provenance,
  not scientific support strength.
- `EvidenceItem.excerpt` is the only content field; nothing records whether that text
  came from metadata, an abstract, or full text.
- `EvidenceItem.kind` collapses `evidence_type` to `literature` / `dataset` /
  `baseline` / `metric`; it says nothing about support strength.

Proposed target:

- An ordered `ScientificSupportLevel` enum: `metadata` < `abstract` < `full_text` <
  `experiment`, attached to each evidence item and each claim.
- Semantic boundaries: `metadata` supports existence and categorization only;
  `abstract` supports a bounded method overview and is insufficient for a complete
  technical-difference claim (the NoveltyGapBuilder rule); `full_text` supports a
  technical-difference claim; `experiment` supports an empirical claim and only from a
  reproducible experiment record produced by this project.

Required contract properties:

- Support level is a total order and is comparable.
- Provenance and support level are orthogonal: a `verified` item can still be
  `metadata`-level and carry only metadata-level support.
- A claim's support level may not exceed the support level of the evidence behind it
  (no upgrade).
- Technical-difference claims require `full_text` or higher; empirical claims require
  `experiment`; existence and categorization claims may rest on `metadata`.

Illegal states to reject:

- A technical-difference claim backed only by `metadata` or `abstract` evidence.
- An empirical claim backed by any non-`experiment` evidence.
- A claim declaring a support level higher than its evidence provides.
- A support level value outside the enum.

Serialization and backward compatibility:

- Implement as `StrEnum` so it serializes to a string; `_jsonable` in `schema.py`
  already handles `StrEnum`.
- `EvidenceItem` is a frozen dataclass constructed in many places (gate, evidence,
  tests). A new field must have a default so existing construction sites keep working.
- Existing `EvidenceItem` JSON has no support-level key. Deserialization needs an
  explicit default. Default to the most conservative level (`metadata`) or an explicit
  `unknown` that forces re-assessment; never default to `full_text` or `experiment`.

Minimum test acceptance:

- `metadata`-only evidence rejected for a technical-difference claim.
- `abstract`-only evidence rejected for a complete technical-difference claim; accepted
  for a bounded overview.
- `full_text` evidence accepted for a technical-difference claim.
- `experiment` evidence accepted for an empirical claim; literature evidence rejected
  for an empirical claim.
- An upgrade attempt (claim level above evidence level) rejected.
- Legacy JSON without the field deserializes to the agreed default.

Undecided implementation details:

- A field on `EvidenceItem` versus a separate mapping.
- Whether `abstract` and `excerpt` are distinguished.
- Whether one item may carry more than one level.
- The exact legacy default (`metadata` versus `unknown`).

## 2. ExperimentEvidenceRecord

Current code facts (stated directly, because the checklist must not overclaim):

- `EvidenceItem.evidence_type` is restricted by `__post_init__` to `prior_work`,
  `limitation`, `dataset`, `baseline`, `metric`. There is no `experiment` type.
- `EvidenceItem.kind` therefore never returns `"experiment"`.
- `EvidenceIndex.verified_experiment_ids()` filters `kind == "experiment"`, so under
  the current schema it always returns an empty tuple.
- In `gate.py`, `experiment_status = VERIFIED if verified_experiment_ids() else PENDING`,
  so `experiment.status` is always `pending` today.
- No field anywhere carries a run id, seed, config, metric values, or dispersion.

Proposed target:

- A separate `ExperimentEvidenceRecord` (not a new `EvidenceItem` type) carrying:
  `research_run_id`; method and baseline identifiers; dataset identifier and its
  provenance; a config snapshot or config hash; seed; metric values; dispersion or
  uncertainty (standard deviation, confidence interval, or run count); analysis method;
  execution status; verification status; and `artifact_path`.
- A defined path by which a record becomes experiment-level evidence: a resolvable
  artifact, a seed, at least one baseline, and metric values traceable to the artifact,
  with a completed execution.
- A defined wiring for `verified_experiment_ids()` to derive from these records rather
  than from `EvidenceItem.kind`.

Required contract properties:

- Only a `verified` `ExperimentEvidenceRecord` may move `experiment.status` from
  `pending` to `verified`.
- Each record binds a single `research_run_id` and a traceable artifact.
- Reported metric values are recomputable or auditable from the artifact
  (the stored-artifact audit level in the paper quality contract).

Illegal states to reject:

- `verified` with no artifact.
- `verified` with no seed.
- `verified` with no baseline.
- `verified` with metric values not traceable to the artifact.
- `execution_status = failed` combined with `verification_status = verified`.
- A reference to a non-existent dataset or method.

Serialization and backward compatibility:

- A new type with its own JSON; do not relax `EvidenceItem`'s five-type validation,
  which would change the meaning of existing bundles.
- To make `verified_experiment_ids()` non-empty, choose deliberately: extend
  `evidence_type` with `experiment` (touches `__post_init__`, `kind`, and tests that
  assume five types) versus add a parallel index over the new records. A parallel index
  is the lower-risk default because it keeps literature and `EvidenceItem` semantics
  intact.
- Until wiring lands, preserve the current always-empty behavior so existing tests that
  assume `pending` do not silently break.

Minimum test acceptance:

- A complete record verifies and moves `experiment.status` to `verified`.
- Missing artifact, missing seed, missing baseline, and untraceable results each reject
  `verified` (four rejection tests).
- A failed execution cannot be `verified`.
- A regression test that, with no records present, `verified_experiment_ids()` is empty
  and `experiment.status` stays `pending`.

Undecided implementation details:

- Extend `evidence_type` versus a parallel record and index (parallel record
  recommended, but decide explicitly).
- Whether verification is structural (fields present, artifact resolvable) or requires
  recomputing a metric.
- The `execution_status` value set.
- How dataset provenance here relates to feasibility evidence (item 5).

## 3. experiment_execution and result_analysis phases

Current code facts:

- `ResearchPhase` has eight values: `ideation`, `value_gate`, `literature`,
  `method_design`, `experiment_design`, `drafting`, `internal_review`,
  `publication_review`. Neither new phase exists.
- `ResearchUsageRecord.__post_init__` calls `ResearchPhase(self.phase)` and raises
  `unsupported phase` for any unknown value, so usage cannot be recorded for the new
  phases until they are added to the enum.
- `aggregate_usage` iterates `for phase in ResearchPhase` to build `by_phase`, so adding
  enum values automatically extends the aggregate output.
- The pipeline is a placeholder after `method_design` (per the paper quality contract).

Proposed target:

- Add `experiment_execution` and `result_analysis` to `ResearchPhase` (proposed).
- Boundaries: `experiment_design` produces a plan and does not run the model;
  `experiment_execution` runs the experiment and produces `ExperimentEvidenceRecord`s
  plus real usage (tokens, tool calls, retries, wall time); `result_analysis` reads
  results and produces a verdict (`supported` / `not_supported` / `inconclusive`),
  dispersion, failure analysis, and the `claim_map`.
- Entry to `drafting` follows the paper quality contract G3: a `verified` record covers
  every required metric and baseline, the result artifact is complete, the `claim_map`
  is built, and statistics and failure analysis are present.
- Return `revise` on undersampling, a failed execution, a default `inconclusive`, a
  missing required baseline or metric, or missing dispersion.

Required contract properties:

- Design, execution, and analysis costs are separately visible; `by_phase` distinguishes
  the three so execution cost is not hidden inside `experiment_design`.
- `experiment_execution` emits at least one `ResearchUsageRecord` of its own (real or
  explicitly `pending`).

Illegal states to reject:

- Recording usage for the new phases before the enum is extended (this raises today, so
  the enum must land first).
- Charging execution or analysis cost to the `experiment_design` phase.
- A `supported` verdict with no `verified` experiment record.
- An `inconclusive` result advancing to `drafting` automatically.

Serialization and backward compatibility:

- Adding enum values does not break existing serialized records (old phases stay valid).
- `aggregate_usage`'s `by_phase` gains two keys; any test asserting exactly eight
  `by_phase` keys must be updated.
- Any hardcoded eight-value phase whitelist elsewhere must be updated in step.

Minimum test acceptance:

- A `ResearchUsageRecord` constructs successfully for each new phase (enum accepts it).
- `aggregate_usage` `by_phase` contains both new keys.
- A `supported` verdict without a `verified` record returns `revise` at G3.
- A default `inconclusive` returns `revise`.
- Execution cost is charged to `experiment_execution`, not `experiment_design`.

Undecided implementation details:

- The exact enum strings.
- Whether phase ordering or dependency is validated explicitly or left to runner order.
- Whether `result_analysis` also carries a pre-`internal_review` self-check.

## 4. claim_map

Current code facts:

- There is no claim structure in the code. The paper quality contract (G3) requires a
  `claim_map` but nothing implements it.
- Available building blocks: `EvidenceItem` / `EvidenceBundle` with `evidence_id`,
  `ValueGateDecision`, and the proposed `ExperimentEvidenceRecord`. Citations are
  described in the paper artifact contract but have no structure yet.

Proposed target (minimum structure):

- `claim_id`, `claim_text`, `claim_type` (for example `motivation`, `related_work`,
  `technical_difference`, `empirical`, `novelty`), `support_level` (item 1),
  `evidence_refs` (`EvidenceItem` ids), `experiment_refs` (`ExperimentEvidenceRecord`
  ids), `citation_refs` (sources inside the bundle), `support_status`
  (`supported` / `insufficient` / `pending`), and an optional `unresolved_objection`.

Required contract properties:

- Every paper claim is traceable to at least one reference.
- An empirical claim may not cite only literature evidence; it needs an
  `experiment_ref`.
- A technical-difference claim may not cite only `metadata` or `abstract` evidence; the
  cited evidence must be `full_text` or higher.
- A claim's support level does not exceed the support level of its cited evidence; the
  rule for combining multiple references must be defined (for example, take the minimum
  upper bound).
- Every referenced id resolves to a known `EvidenceItem`, record, or citation.

Illegal states to reject:

- A non-existent `evidence_id`, `experiment_id`, or citation reference (reuse the
  `referenced_ids - index.ids` missing-id check pattern already in `gate.py`).
- An empirical claim with only literature references.
- A technical-difference claim with only `metadata` or `abstract` references.
- A claim whose support level exceeds its evidence.
- A claim with no reference at all.

Serialization and backward compatibility:

- A new structure with its own JSON; it does not affect existing schemas.
- Reference integrity is validated against `EvidenceBundle.ids()` and the experiment
  record set.

Minimum test acceptance:

- Existence checks for each reference type (unknown id rejected).
- Empirical-with-only-literature rejected.
- Technical-difference-with-metadata rejected.
- Support-level upgrade rejected.
- A valid `claim_map` passes and round-trips through JSON.

Undecided implementation details:

- The `claim_type` value set.
- The support-level combination rule for multiple references.
- Whether a citation is just a reference to an `EvidenceItem` in the bundle.
- Whether the `claim_map` is its own artifact or nested in the `result_analysis`
  artifact.

## 5. feasibility evidence

Current code facts (named directly, because it must not read as implemented):

- In `gate.py`, `feasibility_ok` is `datasets` non-empty and `baselines` non-empty and
  `metrics` non-empty and `feasibility_evidence_ids` non-empty and
  `index.has_verified_literature(feasibility_evidence_ids)`.
- Feasibility is therefore judged through `has_verified_literature()`; the gate checks
  neither dataset access, nor license, nor baseline runnability, nor metric
  measurability.
- `CandidateProblem` carries `datasets` / `baselines` / `metrics` as name-only string
  tuples. `EvidenceItem` has `dataset` / `baseline` / `metric` types but no `access` or
  `license` fields and no runnability or measurability expression.

Proposed target:

- Distinguish six feasibility signals: dataset availability, dataset access, dataset
  license, baseline runnability, metric measurability, and literature support.
- Feasibility may not rest on literature alone; access, license, runnability, and
  measurability each need their own evidence.
- This target must not be written as a current capability, because `gate.py` does not
  perform these checks yet.

Required contract properties:

- Each required dataset has availability, access, and license evidence.
- Each required baseline has runnability evidence.
- Each required metric has measurability evidence.
- Literature support is supplementary, never sufficient on its own.

Illegal states to reject:

- Judging feasible from verified literature alone (the current behavior, which the
  target replaces).
- A dataset with no license or no access.
- A baseline named but with no runnability evidence.
- A metric with no measurability definition.

Serialization and backward compatibility:

- If `access` and `license` become `EvidenceItem` fields, they need defaults and a
  legacy default, and they are meaningful only for the `dataset` type.
- Alternatively, a separate feasibility-evidence record avoids overloading
  `EvidenceItem`; decide explicitly.
- Changing `feasibility_ok` will change existing gate tests (current no_go candidates
  and any pass case). Migrate them in step and keep the current-versus-target split
  explicit, as the paper quality contract already does.

Minimum test acceptance:

- A dataset with no license rejects feasibility.
- A dataset with no access rejects feasibility.
- A baseline with no runnability rejects feasibility.
- A metric with no measurability rejects feasibility.
- Literature-only no longer passes automatically.
- All six signals present passes.

Undecided implementation details:

- `access` and `license` as `EvidenceItem` fields versus a separate record.
- Whether license is checked against an allowed-license set.
- The evidence form for runnability and measurability (offline declaration versus a
  recorded dry run).
- Field reuse with `ExperimentEvidenceRecord` dataset provenance.

## 6. Suggested implementation order

This section suggests an order and its dependencies. It does not implement code. Land
each step as its own commit with its own tests, and add enums and fields before changing
judgment logic so that usage construction never hits an unknown phase.

1. Support level and evidence structure first. Every later item depends on the support
   vocabulary: the experiment level for records, the empirical and technical-difference
   rules for the claim map, and the graded feasibility signals.
2. `ExperimentEvidenceRecord` next, including the deliberate decision on wiring
   `verified_experiment_ids()`. Empirical claims and the execution phase depend on it.
3. Phases and usage next. `experiment_execution` and `result_analysis` are only
   meaningful once experiment records exist to account for.
4. `claim_map` next, once support levels (step 1) and experiment references (step 2) are
   in place to validate the empirical and technical-difference rules.
5. Feasibility checks and the Drafting Gate last. Feasibility touches the existing
   `gate.py` judgment and carries the highest regression risk; the Drafting Gate depends
   on all of the above (experiment records, result artifact, and claim map).

At each step, return to `docs/paper_quality_contract.md` to confirm the scientific rule
the code is meant to enforce.
