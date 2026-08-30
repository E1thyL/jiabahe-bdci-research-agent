# Paper Quality Contract

This document is the quality contract for the research stages that run after the
Research Value Gate returns `go`. It refines `pipeline_contract.md` for the stages
that are currently placeholders in `ResearchPipelineRunner`.

It is a specification, not an implementation. It does not change existing code,
does not select a research topic, and does not call a model, a literature source,
or an external reviewer.

## 0. Existing code versus proposed extensions

This contract separates what the code already enforces from what it proposes. A
rule marked "(proposed)" or "target" is a goal for a later implementation step; it
is not a current capability.

Existing and reused verbatim from the code:

- `ResearchPhase`: `ideation`, `literature`, `value_gate`, `method_design`,
  `experiment_design`, `drafting`, `internal_review`, `publication_review`.
- `GateDecision`: `go`, `revise`, `no_go`.
- `EvidenceStatus`: `verified`, `pending`, `insufficient`. Note: `insufficient` is
  an `EvidenceStatus`, not a `GateDecision`. In the current code an evidence gap is
  reported through per-field states — `ValueGateDecision.literature.status` and
  `ValueGateDecision.experiment.status` — while the gate still returns
  `decision = revise`. There is no single `evidence_status` field today; a unified
  `evidence_status` is proposed for later stage outputs (section 12).
- `EvidenceItem.evidence_type` is restricted to `prior_work`, `limitation`,
  `dataset`, `baseline`, `metric`. Its `kind` view collapses `prior_work` and
  `limitation` to `literature`. There is no `experiment` type, so
  `EvidenceIndex.verified_experiment_ids()` returns empty and `experiment.status`
  stays `pending` under the current schema.
- `MeasurementStatus`: `observed`, `estimated`, `pending`.
- `ScientificSupportLevel`: `metadata`, `abstract`, `full_text`, `experiment` is
  implemented on `EvidenceItem` as a conservative evidence annotation. Legacy
  `EvidenceItem` construction defaults to `metadata`; `LiteratureRecord` propagates
  an explicit level to the materialized item. Claim-level validation and experiment
  records remain proposed.
- `ValueGateDecision`, whose evidence state is exposed only as `literature.status`
  and `experiment.status` (each an `EvidenceStatus`); `ResearchUsageRecord`,
  `aggregate_usage`, and the `topic` policies (`required_baselines`,
  `required_metrics`).

Proposed by this contract and not yet implemented (collected in section 12):

- Claim-level `ScientificSupportLevel` validation and claim/evidence compatibility.
- An `ExperimentEvidenceRecord` to carry experiment provenance.
- Two additional phases, `experiment_execution` and `result_analysis`.
- A unified `evidence_status` for stage outputs.
- Feasibility `access` and `license` evidence and executability checks.
- A drafting-gate `claim_map` and result artifact shape.

The proposed pipeline, with new phases marked, is:

```text
ideation -> literature -> value_gate -> method_design
  -> experiment_design -> experiment_execution (proposed) -> result_analysis (proposed)
  -> drafting -> internal_review -> publication_review
```

## 1. Scientific support level

`verification_status = verified` means the source and its provenance are verified:
a resolvable `source_uri`, a stable `source_hash`, and a replayable record. It does
not mean the paper's conclusions, algorithmic details, or technical differences have
been checked against full text or reproduced. Provenance verification and scientific
support are different axes.

Every `EvidenceItem` now declares a `ScientificSupportLevel`. Claim-level support
annotations and validation are proposed and will be added with `claim_map`. The
current levels are:

- `metadata` (title, authors, venue, year): supports existence and categorization
  only. It cannot support a technical-difference or empirical claim.
- `abstract` (abstract or excerpt): supports a bounded method overview only, and is
  explicitly insufficient for a complete technical-difference claim (the
  NoveltyGapBuilder rule).
- `full_text`: can support a technical-difference claim about prior work.
- `experiment`: reserved for a reproducible experiment record produced by this
  project; the current `EvidenceItem` schema rejects this level and uses the
  proposed `ExperimentEvidenceRecord` instead.

When claim validation is implemented, a claim may not exceed the support level of
the evidence behind it. A `verified` metadata item does not license a full-text
technical-difference claim.

## 2. Stage gates: scientific go to drafting

`go` from the Research Value Gate authorizes design, not writing. `go` also keeps
`experiment.status = pending`; no gate below may treat the hypothesis as proven
until verified experiment records exist.

```text
value_gate = go
  -> [G1 method-entry gate]      -> method_design
  -> [G2 experiment-ready gate]  -> experiment_design -> experiment_execution
                                 -> result_analysis
  -> [G3 drafting gate]          -> drafting
  -> [G4 publication gate]       -> internal_review -> publication_review -> submission
```

Each gate is deterministic and evidence-backed. A gate that does not pass returns
`decision = revise` (fixable) or `decision = no_go`. On a missing-evidence outcome the
gate returns `decision = revise` and the relevant per-field state is `insufficient`
(`literature.status` today; a unified `evidence_status` is proposed, section 12). No
gate fabricates the missing state to move forward.

## 3. Method design entry conditions (G1)

Entry to `method_design` requires all of:

1. A `value_gate` artifact with `decision = go` and empty `reviewer_objections`.
2. Each Value Gate criterion (`significance`, `novelty`, `technical_feasibility`)
   assessed as a pass by the gate. The current gate emits a binary score (4 for a
   pass, 0 otherwise); this contract introduces no new numeric threshold until the
   gate's scoring is calibrated.
3. `closest_prior_work`, `gap`, and `difference` non-empty and backed by `verified`
   `prior_work` / `limitation` evidence at `full_text` support level for any
   technical-difference claim.
4. Feasibility. Target contract: feasibility is backed by executability evidence,
   not literature alone — dataset availability and `license`, dataset `access`,
   baseline runnability, and metric measurability. Current behavior: `gate.py` still
   judges feasibility through `has_verified_literature()` over
   `feasibility_evidence_ids`, plus non-empty `datasets` / `baselines` / `metrics`;
   it does not verify access, license, runnability, or measurability. Those checks
   and the `access` / `license` fields are proposed (section 12), not enforced today.
5. `research_object` and `hypothesis` non-empty and falsifiable.

The `method_design` artifact must contain (proposed; snake_case; carries
`research_run_id`): `hypothesis`, `method_spec`, `baseline_map` (each
`required_baselines` entry mapped to a runnable configuration), `metric_map` (each
`required_metrics` entry mapped to a measurable definition), `evidence_ids`,
`assumptions`, and `threats_to_validity`.

If the method cannot be specified against the topic's required baselines and metrics,
G1 returns `decision = revise`; the pipeline does not advance.

## 4. Experiment design, execution, and completeness (G2)

`experiment_design` and `experiment_execution` are separate phases so that the real
cost and the verified results of running the model are not hidden inside a design
artifact.

`experiment_design` produces a plan. Completeness means all of:

- Coverage: every `required_baselines` and `required_metrics` entry from the `topic`
  policy is present. A missing required baseline or metric is `revise`, not a partial
  pass.
- Comparability: an identical evaluation protocol across the method and every
  baseline. A single-variable change is required only for an ablation that isolates
  the claimed mechanism; distinct baselines are distinct methods and are not held to
  single-variable identity.
- Statistical validity: the number of runs, and a statistical method appropriate to
  the metric type, declared before results are read. Report effect size, a confidence
  interval, or a suitable dispersion measure. A significance test is not mandated for
  every task; it is used where the metric and design warrant it.

`experiment_execution` runs the plan and produces experiment evidence. Only a
`verified` `ExperimentEvidenceRecord` (proposed, section 12) may move
`experiment.status` from `pending` to `verified`. Under the current schema no
experiment evidence can exist, so this phase cannot yet be satisfied.

Reproducibility is stated as three distinct levels, because a fully offline rerun is
not achievable for model-dependent experiments:

- Offline fixture pipeline test: `LITERATURE_MODE = offline` with
  `ReplayLiteratureSource`. This exercises the pipeline without network or key. It
  reproduces the literature path only; it does not reproduce a DeepSeek V4 Flash
  experiment.
- Controlled experiment reproduction: rerunning the scientific experiment requires
  the official DeepSeek V4 Flash endpoint and key. It is not offline and must record
  real usage.
- Stored-artifact audit: verifying results against previously stored artifacts under
  `research_run_id`, without rerunning.

Resource accounting: each phase emits one or more `ResearchUsageRecord`s, aggregated
to a phase-level summary (`aggregate_usage` by phase). `experiment_execution` records
its own tokens, tool calls, retries, and wall time separately from design.
Deterministic replay may record zero tool calls but must state that it is not a live
search.

## 5. Result analysis standard (result_analysis)

`result_analysis` is a distinct phase. For each hypothesis it must state:

- Metric values for the method and every baseline, with dispersion and the outcome of
  the pre-declared statistical method (effect size, a confidence interval, or a
  suitable dispersion measure).
- A verdict mapped to the hypothesis: `supported`, `not_supported`, or
  `inconclusive` — never mapped to a desired narrative.
- Ablations that isolate the claimed mechanism.
- Failure and limitation analysis, including where the method underperforms a
  baseline.
- Every numeric claim traceable to a stored run artifact under `research_run_id`, at
  `experiment` support level.

No result may be reported that is not reproducible from a stored artifact. A metric
improvement reported without dispersion or an appropriate statistical method returns
`decision = revise` (evidence state `insufficient`), not a positive result.

## 6. Negative-result and honesty rules

The pipeline returns a truthful state rather than a fabricated success.

- `not_supported` is a valid, publishable outcome and proceeds to drafting as a
  negative or null result, but only when the experiment is sufficient (required
  baselines and metrics covered, enough runs for the declared method), the hypothesis
  was declared in advance, and the conclusion is interpretable.
- `inconclusive` does not automatically proceed to drafting. Undersampling, execution
  failure, or an insensitive metric return `decision = revise`. An `inconclusive`
  result may proceed only when it is itself a sufficient, interpretable scientific
  finding, and that justification is explicit.
- The system never converts `insufficient` evidence, a `pending` experiment, or a
  failed search into a `verified` or positive claim.
- Search `failed` / `empty` / `partial` states and record-level incompleteness stay
  distinguishable; none of them yields `verified` evidence or a citation.
- A run that cannot reach a defensible paper returns `decision = revise` at the
  pipeline boundary (evidence state `insufficient` when the cause is missing evidence)
  instead of emitting a low-quality draft.

## 7. Claim-evidence-citation constraint

Every claim in the paper binds to evidence and declares its support level (section 1).

- Related-work and motivation claims bind to `EvidenceItem`s with
  `verification_status = verified`, referenced by `evidence_id`, carrying `source_uri`
  and a non-empty `source_hash`. A technical-difference claim requires `full_text`
  support; `metadata` or `abstract` support cannot carry it.
- Empirical claims bind to a `verified` `ExperimentEvidenceRecord` (proposed) under
  the same `research_run_id`, at `experiment` support level.
- Novelty claims bind to `closest_prior_work` plus an explicit `gap` and `difference`;
  a missing or `pending` prior work yields an `insufficient` or `pending` gap, never a
  fabricated novelty statement.
- No citation may point to a source absent from the `EvidenceBundle`. An uncited
  quantitative or comparative claim fails the drafting gate (G3).
- Citations resolve to real, retrievable sources. A source that cannot be re-fetched
  or replayed from its provenance is not `verified`.

## 8. Drafting gate entry conditions (G3)

Entry to `drafting` requires all of:

1. `experiment_execution` complete, with a `verified` `ExperimentEvidenceRecord`
   (proposed) covering every required metric for every required baseline, so that
   `experiment.status = verified`.
2. A complete result artifact: for each hypothesis, a verdict plus metric values,
   dispersion, and the outcome of the pre-declared statistical method (section 5).
3. A `claim_map` (proposed): every claim intended for the paper mapped to its
   `evidence_id` or experiment record and its declared support level.
4. Statistics and failure analysis present: runs, dispersion, and the chosen
   statistical method recorded; failure and limitation analysis on file.

If any condition fails, G3 returns `decision = revise` and names the missing artifact.
`go` from the Value Gate is not sufficient for drafting on its own.

## 9. Internal reviewer rubric (part of G4)

The paper's primary rubric follows common ICLR review standards, scored 0-5 per
dimension:

| Dimension | Question | Fail (score < 3) |
|---|---|---|
| Soundness | Are claims supported by reproducible evidence at the right support level? | any uncited empirical claim |
| Originality | Is there an explicit, evidence-backed gap and difference? | novelty asserted from metadata only |
| Significance | Does the result matter beyond one narrow case? | single-case result generalized without support |
| Clarity | Is the method and evaluation stated precisely? | key protocol undefined |
| Reproducibility | Can a reader rerun or audit at one of the three levels? | missing seeds, config, or corpus |
| Limitations | Are negatives, limits, and resource costs disclosed? | hidden negative result or omitted cost |

Overall `pass` requires no dimension below 3 and zero unresolved `reviewer_objections`.
Each objection maps to a claim, an `evidence_id`, or a missing artifact — never a
subjective note. A failing review returns `decision = revise` and names the artifact
to fix.

Competition scoring is tracked separately from the paper rubric. The official score
uses four weighted items:

| Scored item | Weight | Governed by |
|---|---|---|
| Paper quality | 60 | this rubric |
| Agent system capability | 15 | system and framework evidence |
| Resource consumption (efficiency) | 10 | the resource report (section 13) |
| openJiuwen contribution | 15 | framework contribution material |

These four items are the total score; nothing replaces them. The seven review focuses
(maturity, advancedness, novelty, practicality, generality, social benefit, commercial
value) are auxiliary observation dimensions for paper quality and expert review only;
they do not substitute for the four scored items.

Internal review is deterministic and offline in this contract. The external Stanford
Agentic Reviewer is a later, separate gate and is not invoked here.

## 10. ICLR paper artifact contract

The `drafting` and `publication_review` output is an English, ICLR-style short paper.
The artifact carries `research_run_id` and must include:

- Standard sections: Abstract, Introduction, Related Work, Method, Experiments,
  Results, Limitations, Conclusion, References.
- Claims in every section satisfying the claim-evidence-citation constraint
  (section 7).
- A results section reporting the pre-declared metrics with dispersion, including any
  negative result.
- A references list drawn only from `verified` `EvidenceBundle` items.
- A reproducibility appendix stating all three levels (section 4): the offline fixture
  test, the controlled experiment reproduction with its model-endpoint dependency, and
  the stored-artifact audit; with seeds, configs, corpus identifier, `LITERATURE_MODE`,
  and the rerun or audit procedure for each applicable level.
- A resource report aggregated from the phase-level `ResearchUsageRecord` summaries,
  with honest statuses.

Submission closure, the exit of the publication gate, requires the compiled English
PDF against the official ICLR template and a Reviewer Access Token that matches that
exact PDF. A PDF without a matching token, or a token without a resolvable PDF, does
not pass.

## 11. Publication gate (G4) and submission

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

## 12. Proposed schema extensions

These are proposed by this contract and are not implemented. They are the work items a
later implementation step must land; naming and shape are indicative.

- Claim-level `ScientificSupportLevel` validation and claim/evidence compatibility.
  Evidence-level support annotations are implemented; claim-level enforcement is
  still proposed (section 1).
- `ExperimentEvidenceRecord`: the current `EvidenceItem.evidence_type` has no
  `experiment` value and `kind` never resolves to `experiment`, so
  `verified_experiment_ids()` is always empty and `experiment.status` is always
  `pending`. A separate record must carry experiment provenance: `research_run_id`,
  method and baseline identifiers, config, seed, metric values, dispersion, and the
  statistical outcome, with its own `verification_status`.
- Two phases in `ResearchPhase`: `experiment_execution` and `result_analysis`. Without
  them, real experiment cost and result quality are hidden inside `experiment_design`.
- A unified `evidence_status` for stage outputs. Today evidence state is exposed only
  as `ValueGateDecision.literature.status` and `experiment.status`; there is no single
  `evidence_status` field.
- Feasibility `access` and `license` evidence plus dataset, baseline, and metric
  executability checks. Today `gate.py` judges feasibility via
  `has_verified_literature()` and does not verify access, license, runnability, or
  measurability.
- A `claim_map` structure and a result artifact shape for the drafting gate
  (section 8).

## 13. Traceability and usage

- Every stage emits an artifact dict with `research_run_id` and one or more
  `ResearchUsageRecord`s, aggregated to a phase-level summary.
- `observed` requires provider-returned input and output tokens; otherwise the record
  is `estimated` (with a stated basis) or `pending` with `null` tokens.
- `aggregate_usage` totals treat `pending` as unknown and contribute zero, not
  observed zero.
- The final resource report is reconstructable purely from stored records under
  `research_run_id`.
