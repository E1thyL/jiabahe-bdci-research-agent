# Paper Quality Contract

This document is the quality contract for the research stages that run after the
Research Value Gate returns `go`. It refines `pipeline_contract.md` for the stages
that are currently placeholders in `ResearchPipelineRunner`:

```text
method_design -> experiment_design -> drafting -> internal_review -> publication_review
```

It is a specification, not an implementation. It does not change existing code,
does not select a research topic, and does not call a model, a literature source,
or an external reviewer. Every rule here inherits the guarantees already enforced
upstream:

- Stage artifacts are dictionaries carrying `research_run_id`.
- A judgment may only reference `evidence_id` values present in the `EvidenceBundle`.
- A `revise` or `no_go` result returns before method design and is never silently
  promoted to a paper.
- Resource records use `observed` / `estimated` / `pending` and never write unknown
  tokens as `observed 0`.

Decision vocabulary is reused verbatim from the code:

- `GateDecision`: `go`, `revise`, `no_go`
- `EvidenceStatus`: `verified`, `pending`, `insufficient`
- `MeasurementStatus`: `observed`, `estimated`, `pending`
- `ResearchPhase`: `ideation`, `literature`, `value_gate`, `method_design`,
  `experiment_design`, `drafting`, `internal_review`, `publication_review`

## 1. Stage gates: scientific go to drafting

`go` from the Research Value Gate authorizes design, not writing. Four gates stand
between a scientifically approved candidate and a submitted paper.

```text
value_gate = go
  -> [G1 method-entry gate]      -> method_design
  -> [G2 experiment-ready gate]  -> experiment_design + execution
  -> [G3 drafting gate]          -> drafting
  -> [G4 publication gate]       -> internal_review -> publication_review -> submission
```

Each gate is deterministic and evidence-backed. A gate that does not pass returns
`revise` (fixable) or reports `insufficient` (evidence missing); it never fabricates
the missing state to move forward. `go` from the Value Gate keeps
`experiment.status = pending`: no gate below may treat the hypothesis as proven
until verified experiment records exist.

## 2. Method design entry conditions (G1)

Entry to `method_design` requires all of:

1. A `value_gate` artifact with `decision = go` and empty `reviewer_objections`.
2. Each Value Gate criterion (`significance`, `novelty`, `technical_feasibility`)
   assessed ok, `score >= 3` on the 0-5 `CriterionAssessment` scale (the current
   gate emits 4 for a pass), each backed by `verified` literature evidence.
3. `closest_prior_work`, `gap`, and `difference` non-empty and backed by `verified`
   `prior_work` / `limitation` evidence, per the NoveltyGapBuilder rules.
4. `datasets`, `baselines`, and `metrics` non-empty and consistent with the `topic`
   policy's `required_baselines` and `required_metrics`.
5. `research_object` and `hypothesis` non-empty and falsifiable.

The `method_design` artifact must contain (proposed contract; snake_case; carries
`research_run_id`):

- `hypothesis`: the falsifiable claim the experiment will test.
- `method_spec`: the mechanism, its inputs and outputs, and the component under study.
- `baseline_map`: each `required_baselines` entry mapped to a concrete, runnable
  configuration.
- `metric_map`: each `required_metrics` entry mapped to a measurable definition.
- `evidence_ids`: the `verified` evidence supporting feasibility.
- `assumptions` and `threats_to_validity`.

If the method cannot be specified against the topic's required baselines and metrics,
G1 returns `revise`; the pipeline does not advance.

## 3. Experiment completeness requirements (G2)

`experiment_design` must produce a plan that a third party can rerun offline.
Completeness means all of:

- Coverage: every `required_baselines` and `required_metrics` entry from the `topic`
  policy is present. A missing required baseline or metric is `revise`, not a partial
  pass.
- Reproducibility: fixed random seeds, dataset identifiers with provenance
  (`source_uri`, `source_hash`), an environment and config snapshot, and a
  deterministic offline path (`LITERATURE_MODE = offline` with
  `ReplayLiteratureSource`) that needs no network or key.
- Comparability: an identical evaluation protocol across the method and every
  baseline, with a single-variable change per comparison.
- Statistical validity: the number of runs, a dispersion measure (standard deviation
  or confidence interval), and the significance test all declared before results are
  read.
- Resource accounting: one `ResearchUsageRecord` per phase with `research_run_id` and
  an honest `measurement_status`. Deterministic replay may record zero tool calls but
  must state that it is not a live search.

Experiment execution produces verified experiment evidence. Only then may a
downstream artifact set `experiment.status = verified`; absent that, it stays
`pending`.

## 4. Result analysis standard

The result analysis for each hypothesis must state:

- Metric values for the method and every baseline, with dispersion and the outcome of
  the pre-declared test.
- A direct verdict mapped to the hypothesis: `supported`, `not_supported`, or
  `inconclusive` — never mapped to a desired narrative.
- Ablations that isolate the claimed mechanism.
- Failure and limitation analysis, including where the method underperforms a
  baseline.
- Every numeric claim traceable to a stored run artifact under `research_run_id`.

No result may be reported that is not reproducible from a stored artifact. A metric
improvement reported without dispersion or a test is `insufficient`, not a positive
result.

## 5. Negative-result and honesty rules

The pipeline returns a truthful state rather than a fabricated success.

- A hypothesis with a `not_supported` or `inconclusive` analysis is a valid,
  publishable outcome. It proceeds to drafting as a negative or null result, framed as
  such.
- The system never converts `insufficient` evidence, a `pending` experiment, or a
  failed search into a `verified` or positive claim.
- If required baselines or metrics cannot be produced, the stage returns `revise`
  (recoverable) or reports `insufficient` (evidence gap) and names the missing item.
- Search `failed` / `empty` / `partial` states and record-level incompleteness stay
  distinguishable; none of them yields `verified` evidence or a citation.
- A run that cannot reach a defensible paper returns `revise` or `insufficient` at the
  pipeline boundary instead of emitting a low-quality draft.

## 6. Claim-evidence-citation constraint

Every claim in the paper binds to evidence.

- Related-work and motivation claims bind to `EvidenceItem`s with
  `verification_status = verified`, referenced by `evidence_id`, carrying `source_uri`
  and a non-empty `source_hash`. Title or metadata alone cannot support a
  technical-difference claim.
- Empirical claims bind to a stored experiment run artifact under the same
  `research_run_id`.
- Novelty claims bind to `closest_prior_work` plus an explicit `gap` and `difference`;
  a missing or `pending` prior work yields an `insufficient` or `pending` gap, never a
  fabricated novelty statement.
- No citation may point to a source absent from the `EvidenceBundle`. An uncited
  quantitative or comparative claim fails the drafting gate (G3).
- Citations resolve to real, retrievable sources. A source that cannot be re-fetched
  or replayed from its provenance is not `verified`.

## 7. Internal reviewer rubric (part of G4)

`internal_review` scores the draft on a 0-5 scale per dimension. The first seven
dimensions align with the official evaluation axes; the last two are the project's
non-negotiable process floor.

| Dimension | Question | Fail (score < 3) |
|---|---|---|
| Maturity | Are claims supported by reproducible evidence? | any uncited empirical claim |
| Advancedness | Is the method beyond the closest prior work? | no measured gain over a required baseline |
| Novelty | Is there an explicit, evidence-backed gap and difference? | novelty asserted from title or metadata only |
| Practicality | Is the setup runnable and the cost reported? | no resource report or unrunnable setup |
| Generality | Does the claim hold beyond one narrow case? | single-case result generalized without support |
| Social benefit | Is the stated impact concrete, not speculative? | impact claimed without a described scenario |
| Commercial value | Is applicability stated without overclaiming? | value asserted with no basis |
| Reproducibility | Can a reader rerun offline? | missing seeds, config, or corpus |
| Honesty | Are negatives, limits, and resource costs disclosed? | hidden negative result or omitted cost |

Overall `pass` requires no dimension below 3 and zero unresolved `reviewer_objections`.
Each objection maps to a claim, an `evidence_id`, or a missing artifact — never a
subjective note. A failing review returns `revise` and names the specific artifact to
fix; it does not block indefinitely without a stated reason.

Internal review is deterministic and offline in this contract. The external Stanford
Agentic Reviewer is a later, separate gate and is not invoked here.

## 8. ICLR paper artifact contract

The `drafting` and `publication_review` output is an English, ICLR-style short paper.
The artifact carries `research_run_id` and must include:

- Standard sections: Abstract, Introduction, Related Work, Method, Experiments,
  Results, Limitations, Conclusion, References.
- Claims in every section satisfying the claim-evidence-citation constraint
  (section 6).
- A results section reporting the pre-declared metrics with dispersion, including any
  negative result.
- A references list drawn only from `verified` `EvidenceBundle` items.
- A reproducibility appendix: seeds, configs, the corpus identifier, `LITERATURE_MODE`,
  and the offline rerun command.
- A resource report aggregated from `ResearchUsageRecord`s (per-phase input and output
  tokens, tool calls, retries, wall time, reviewer calls) with honest statuses.

Submission closure, the exit of the publication gate, requires the compiled English
PDF against the official ICLR template and a Reviewer Access Token that matches that
exact PDF. A PDF without a matching token, or a token without a resolvable PDF, does
not pass.

## 9. Publication gate (G4) and submission

```text
draft
  -> internal_review     (rubric pass, objections resolved)
  -> publication_review  (artifact contract complete)
  -> external reviewer   (later; not in this contract)
  -> submission package  (ICLR PDF + matching Reviewer Access Token + resource report)
```

Submission must run from an approved local corpus and must not treat the public
network as a survival condition. Whether submission-time external access is permitted
follows the official written answer; until then, the default path is offline.

## 10. Traceability and usage

- Every stage emits an artifact dict with `research_run_id` and one
  `ResearchUsageRecord`.
- `observed` requires provider-returned input and output tokens; otherwise the record
  is `estimated` (with a stated basis) or `pending` with `null` tokens.
- `aggregate_usage` totals treat `pending` as unknown and contribute zero, not
  observed zero.
- The final resource report is reconstructable purely from stored records under
  `research_run_id`.
