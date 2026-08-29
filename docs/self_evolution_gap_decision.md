# Self-evolution final gap decision

Run: `self-evolution-gap-decision-20260829`  
Candidate: **Review-gated reversible Skill evolution for long-horizon Agent
research tasks**  
Date: 2026-08-29

## Decision

```ini
self_evolution = no_go
method_design = not_allowed
```

The candidate currently combines self-reflection, prompt/skill generation,
testing, reviewer approval, and rollback. The full-text review found strong
precedents for the first three components and no evidence that “review gate” or
“rollback” is an independent update-selection algorithm. A human approval
button and version-control revert are valuable system engineering, but are not
by themselves a paper-level scientific contribution.

## Candidate and decision test

Working problem: can review-gated reversible Skill updates improve capability
on long-horizon Agent tasks without propagating unsafe changes?

Required scientific difference would be an algorithm that selects, tests,
approves, deploys, and possibly reverses updates based on measurable expected
capability gain and propagation risk. The current proposal specifies the
lifecycle but not such a selection rule. In particular, these are insufficient
on their own:

```text
self-reflection + Skill/prompt generation
generated tests + reviewer approval
version history + rollback
```

## Controlled retrieval

The four queries were:

```text
self-evolving LLM agents skill acquisition
agent skill evolution with evaluation
reversible agent policy or tool evolution
review-gated autonomous agent improvement
```

Each query used one page, a 10-second timeout, and at most one retry. The first
retrieval attempt encountered one incomplete OpenAlex response; the bounded
transport wrapper converted it to a retryable failure without changing
production code. The successful bounded run made 4 HTTP requests and took
approximately 9,420 ms; including the preceding failed transport attempt, the
total wire-attempt count was 5. Results were 24, 20, 22, and 24 normalized
records, all `partial`. Raw snapshots are local ignored artifacts under
`.pilot-cache/self-evolution-gap-decision-20260829/`.

The queries were noisy. They returned generic autonomous-agent surveys,
unrelated skill-economics papers, classical mobile-agent security, and general
policy literature. They did not return a direct review-gated reversible Skill
evolution paper.

## Full-text verification

### Promptbreeder

Paper: *Promptbreeder: Self-Referential Self-Improvement Via Prompt Evolution*  
Evidence ID: `openalex:3d8d17aad06f6536`  
Source URI: `http://arxiv.org/abs/2309.16797`  
Full-text URI: `https://arxiv.org/pdf/2309.16797`  
Source hash: `3d8d17aad06f65361f2933a9e04df55258772e02f79664e0b2d02fc8bba36f32`

`source_verified=true`; `scientifically_verified=true` for these limited
claims:

- Abstract, p. 1: Promptbreeder evolves task-prompts and mutation-prompts,
  evaluates fitness on a training set, and repeats over generations.
- Section 3, p. 5: the evolved object is a text prompt strategy, not a runtime
  Skill package or tool implementation.
- Section 3.2, pp. 6-8: direct mutation, hypermutation, and Lamarckian mutation
  provide explicit update/generation operators; fitness-proportionate selection
  chooses candidates.
- Table 1, p. 2 and Section 4, pp. 9-10: evaluation uses mathematical,
  commonsense, and hate-speech datasets with accuracy-style metrics and prompt
  baselines.
- Appendix F, p. 23: the paper explicitly describes causal self-reference in
  prompt and mutation-prompt evolution.

Promptbreeder has no reviewer approval gate, rollback protocol, unsafe Skill
propagation metric, or long-horizon Agent deployment setting in the inspected
text. It nevertheless proves that automated self-improvement and update
selection are already algorithmic research topics; “evolve prompts” cannot be
presented as a new Skill-evolution mechanism.

### Agent Hospital

Paper: *Agent Hospital: A Simulacrum of Hospital with Evolvable Medical Agents*  
Evidence ID: `openalex:ed192b83a1144141`  
Source URI: `http://arxiv.org/abs/2405.02957`  
Full-text URI: `https://arxiv.org/pdf/2405.02957`  
Source hash: `ed192b83a11441410452eeb7fefe9e5a807fc59c011c7f9a79b27bfe1b894801`

`source_verified=true`; `scientifically_verified=true` for these limited
claims:

- Abstract, pp. 1-3: Agent Hospital uses a simulacrum and SEAL to evolve
  doctor agents through generated medical cases and treatment interactions.
- Figure 1 and p. 2: multiple doctor, nurse, and patient agents operate in a
  closed virtual hospital cycle; the setting is multi-agent, though the
  evolving doctor capability is evaluated as an agent capability.
- p. 7 and Appendix B, pp. 17-18: the experience base accumulates failures;
  experience reflection, validation, and refinement turn incorrect answers
  into natural-language principles. A quality-control agent validates generated
  medical cases.
- Figure 5, p. 8 and pp. 20-23: virtual and real-world/MedQA evaluations report
  diagnostic accuracy as experience accumulates, with ablations over case and
  experience retrieval.
- p. 10: the paper positions virtual-environment evolution as a way to
  accelerate capability improvement and discusses limitations of isolated task
  studies.

Agent Hospital contains automated validation and learning from failures, but no
  general review-gated Skill update selection, rollback after deployment, or
  explicit error-propagation metric. It shows that “generate experience, test,
  refine, and measure capability gain” is already a substantial prior.

### Reflexion

Paper: *Reflexion: Language Agents with Verbal Reinforcement Learning*  
Evidence ID: `openalex:a1e447b1871fd54d`  
Source URI: `http://arxiv.org/abs/2303.11366`  
Full-text URI: `https://arxiv.org/pdf/2303.11366`  
Source hash: `a1e447b1871fd54d0c4bdeec6e100b45590d4e12422ae471fdcf4eb02934a846`

`source_verified=true`; `scientifically_verified=true` for these limited
claims:

- Abstract and pp. 1-2: Reflexion converts environmental feedback into verbal
  feedback and adds the resulting summary to future context without changing
  model weights.
- Algorithm 1 and p. 4: an Actor generates a trajectory, an Evaluator scores
  it, and a Self-Reflection model appends feedback to long-term memory over
  repeated trials.
- p. 5: short-term trajectory memory and long-term reflective memory are
  combined to improve subsequent decisions.
- Figures 3-4, pp. 6-7 and Tables 2/5, pp. 8/12: ALFWorld, HotPotQA,
  HumanEval, and MBPP provide success, accuracy, and unit-test outcomes.
- Section 5, p. 9 and Appendix B.1, p. 14: local minima, limited sliding-window
  memory, weak self-reflection, and difficulty with exploration are documented
  limitations.

Reflexion provides automated evaluation and self-reflective update, but no
  reviewer gate, rollback, Skill package deployment, or unsafe propagation
  control. It directly overlaps the proposed “self-reflection + test feedback +
  update” pipeline.

## Overlap matrix

`Yes` means supported by full-text inspection. `No` means the inspected text did
not establish that capability; it does not prove the paper cannot implement it.

| dimension | Promptbreeder | Agent Hospital | Reflexion | candidate |
|---|---|---|---|---|
| what evolves | task and mutation prompts | doctor-agent experience/capability | verbal reflections and future policy context | Skills/tool procedures |
| update/generation | mutation, hypermutation, Lamarckian operators | generated cases, reflection, validation, refinement | evaluator feedback to reflection memory | review-gated Skill update |
| evaluation mechanism | fitness on labeled tasks | quality control plus diagnostic accuracy | environment evaluator plus tests/rewards | capability and safety evaluator |
| test/benchmark | MultiArith, GSM8K, ETHOS and others | virtual hospital and MedQA | ALFWorld, HotPotQA, HumanEval, MBPP | long-horizon research tasks |
| deployment timing | candidate prompt generations | virtual training then real-world MedQA test | next trial/episode context | approved Skill deployment |
| failure containment | fitness selection only | validation of generated cases | evaluator feedback; no rollback | invalid activation and propagation control |
| rollback/reversibility | No evidence | No evidence | No evidence | Required |
| human/automated review | automated fitness | automated validation | automated evaluator | reviewer gate plus tests |
| resource cost | repeated LLM mutation/fitness evaluations | large synthetic simulation and training | repeated trials and reflections | update, test, review, rollback overhead |
| multi-agent/single-agent | single LLM prompt evolution | multi-agent simulation | single-agent task loops | long-horizon multi-agent target |

## Real technical gap

The literature supports three established families: evolutionary prompt
optimization, environment-mediated capability evolution with validation, and
feedback-based self-reflection. None of the three inspected papers establishes
the exact combination of Skill package deployment, reviewer approval, rollback,
and unsafe-propagation measurement. However, that absence is not yet a gap
because the candidate supplies no new update-selection rule. Review approval is
currently a human process boundary, and rollback is currently version-control
reversion.

The minimum new algorithm would need to select updates using predicted
capability gain and propagation risk, define a testable acceptance criterion,
and trigger a reversible deployment action. It would also need to show that its
behavior is not equivalent to Promptbreeder fitness selection, Agent Hospital
validation/refinement, or Reflexion's evaluator feedback. No such mechanism was
found in this review.

## Baselines, metrics, and scientific decision

Potential baselines are `static_skill_set`, `self_reflection_only`,
`fitness_selected_prompt_or_skill_update`, and `update_with_tests_without_gate`.
Potential metrics are capability gain, regression rate, invalid Skill
activation rate, rollback success rate, error propagation rate, task success,
and token/latency overhead. These make a future experiment feasible but do not
turn lifecycle controls into a novel algorithm.

The scientific decision is therefore:

```json
{
  "self_evolution": "no_go",
  "reason": [
    "self-improvement and prompt/skill-like evolution already have algorithmic precedents",
    "automated evaluation and failure-derived updates already have direct precedents",
    "review approval is currently a process gate, not a new selection algorithm",
    "rollback is currently version control, not a demonstrated learning mechanism",
    "error propagation and capability gain are not linked by a new measurable update rule"
  ]
}
```

## Resource record

The successful OpenAlex collection used 4 query calls and approximately 9,420
ms. There was one preceding incomplete-response wire attempt, making 5 total
wire attempts; it was not persisted as an accepted adapter retry. Token counts
were unavailable, so the successful collection record uses
`phase=literature`, `measurement_status=estimated`, `tool_calls=4`,
`retry_count=0`, `wall_time_ms=9420`, with null input/output tokens. No model or
reviewer call was made.

## Final routing

All three candidate directions are now `no_go`: `memory_engine`,
`context_engineering`, and `self_evolution`. Method Design remains forbidden.
The next task must be a strategic redefinition of a genuinely narrow research
question, not further packaging of the current three themes.
