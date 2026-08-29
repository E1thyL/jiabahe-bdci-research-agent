# Memory-engine final gap decision

Run: `memory-gap-decision-20260829`  
Candidate area: memory engine  
Date: 2026-08-29

## Decision

```ini
candidate_A_source_aware_memory = no_go
candidate_B_evidence_constrained_selective_update = no_go
memory_engine = no_go
method_design = not_allowed
```

This is a deliberate stop, not a claim that provenance is unimportant. The
available evidence shows strong overlap between long-horizon memory management,
selective update, and provenance capture, but does not establish a new
algorithmic mechanism for the proposed combination in Agent research tasks.
Continuing to add fields, prompts, or more broad search results would be
packaging rather than research progress.

## Davis full-text recovery

Paper: *Data Provenance for Multi-Agent Models in a Distributed Memory*  
Evidence ID: `openalex:468ccacc948c31da`  
Source URI: `http://hdl.handle.net/1773/40436`  
Full-text URI: `https://digital.lib.washington.edu/bitstreams/7b42602a-f437-47f6-bd23-d14ee16bcf20/download`  
OpenAlex evidence hash: `468ccacc948c31dacc790d1abb5eaa32364dd3e3990ac75f45003720f4498579`  
Downloaded PDF SHA-256: `80DB2D4945964B05DD0A22B8FF05BB62DA02AC119192F87D3242FF1D61AC4F52`

`source_verified=true` and `scientifically_verified=true` now apply to the
limited claims below. This is not an LLM memory paper, so it cannot by itself
support the candidate's novelty.

| section/page | original excerpt | verified conclusion |
|---|---|---|
| Abstract, p. iii | “data provenance can support agent-based modeling by explaining individual agent behavior” and ProvMASS captures MAM provenance in distributed memory | Provenance is used to explain multi-agent model behavior; the setting is distributed simulation, not research-agent memory |
| Introduction, pp. 1-2 | the thesis addresses provenance of shared resources, individual agent behavior, and coordination of distributed data | The problem is provenance capture and explanation, not selective language-memory consolidation |
| Contributions, pp. 6-7 | ProvMASS represents causally ordered concurrent events around consistently identified distributed data in a directed provenance graph | This is a concrete provenance representation and causal-order mechanism; it is much more than a `source_id` field, but it operates on execution/data events |
| Evaluation, pp. 63-73 | queries cover individual behavior, simulation specification/execution, and distributed execution | Evaluation is query-based explanation of SugarScape and RandomWalk simulations, not long-horizon LLM task success or unsupported claims |
| Performance, pp. 75-86 | agent-scale and pause-provenance comparisons measure overhead as agents, places, and iterations scale | Provenance cost is an explicit trade-off in this prior; candidate token/latency claims would need to beat or adapt this idea |
| Conclusion, p. 87 | ProvMASS captures provenance sufficient to explain behavior and relate it to framework execution traces and source code | Source/execution attribution is already a substantive prior concept; the candidate cannot claim attribution as novel by itself |

The PDF's representation is a directed provenance graph over causal events and
distributed resources. Its update/capture policy is adaptive instrumentation;
queries retrieve graph relationships. The work does not provide an LLM memory
write policy, language-model retrieval policy, long-horizon research benchmark,
or unsupported-claim metric. Those absent capabilities are evidence about the
scope of this prior, not a complete novelty gap.

## Four-query follow-up

The exact queries were:

```text
provenance-aware memory for language model agents
source attribution long-horizon agents
unsupported claim control agent memory
multi-agent research memory provenance
```

Each query used one page, a 10-second timeout, and at most one retry. All four
returned `partial`, with 23, 22, 24, and 23 normalized records. There were 4
OpenAlex HTTP requests, 0 retries, and approximately 10,522 ms total wall time.
Snapshots are retained locally under:

```text
.pilot-cache/memory-gap-decision-20260829/
```

The results did not produce a directly relevant, full-text-available LLM
memory/provenance work. They returned generic provenance systems, unrelated
uses of “attribution”, and general agent material. A notable provenance failure
was the OpenAlex item titled *Persistent memory for AI coding agents: a
pre-registered SWE-bench Verified benchmark* with URI
`http://arxiv.org/abs/2310.06770`. Downloading that URI yielded the unrelated
ICLR 2024 *SWE-bench: Can Language Models Resolve Real-World GitHub Issues?*
PDF. The record is therefore excluded from novelty evidence. This demonstrates
why an OpenAlex title and URI pair must be checked against the actual full text.

## Candidate A: source-aware memory

Definition: each memory unit stores a source URI, evidence excerpt, and
attribution metadata.

This is `no_go`. ProvMASS already demonstrates meaningful provenance graphs and
source/execution relationships, while the candidate definition itself only
adds provenance fields to an existing memory representation. Without a new
memory operation, causal attribution algorithm, or experimentally distinct
failure-control mechanism, this is a data-structure extension. The candidate
cannot claim novelty from `ordinary memory + source_id + citation field`.

## Candidate B: evidence-constrained selective memory update

Definition: the Agent uses evidence quality, source reliability, and future task
value to decide what enters long-term memory, what is rejected, and what is
forgotten, then measures unsupported claims and resource cost.

This is also `no_go` at the current decision point. MMPO already provides a
learned memory-policy optimization signal for recursive summaries on
long-horizon tasks. HiAgent already provides subgoal-based summarization and
selective trajectory retrieval on long-horizon tasks. ProvMASS provides a
substantive provenance and overhead prior. The four focused queries did not
provide full-text evidence of a distinct evidence-gating update algorithm in a
multi-agent research setting. Therefore Candidate B currently combines known
components without a demonstrated new mechanism.

The candidate could only be reconsidered as a new project if a future review
defines and implements all of the following as an algorithm rather than a
prompt or schema:

```text
memory update mechanism
evidence gating rule
source reliability and conflict handling
rejection / forgetting operation
at least two executable baselines
unsupported-claim and attribution metrics
long-horizon research-task benchmark
token and latency trade-off
```

That is a new research program, not an approved continuation of this candidate.

## Overlap matrix

`Yes` means supported by full-text inspection. `Pending` means the dimension
was not established for that paper. “Candidate” describes the desired scope,
not an achieved capability.

| dimension | ProvMASS / Davis | MMPO | HiAgent | Candidate B |
|---|---|---|---|---|
| long-horizon task | No | Yes | Yes | Yes |
| selective write/update | adaptive provenance capture | learned memory-policy supervision | subgoal summary/replacement and selective retrieval | evidence-gated update |
| provenance tracking | Yes, directed causal graph | No evidence | No evidence | Required |
| source attribution | Yes, execution/source relationships | No evidence | No evidence | Required |
| forgetting/consolidation | capture filtering, not LLM forgetting | recursive summary | summarized completed subgoals | Required |
| multi-agent research | multi-agent simulation, not research agents | No evidence in inspected evaluation | No evidence in inspected evaluation | Required |
| unsupported claim control | No | No | No | Required |
| evaluation | provenance queries, agent-scale overhead | accuracy, EM/F1, reward | SR, PR, steps, context, time | unsupported-claim rate, attribution accuracy, success, cost |

The remaining intersection is a plausible engineering objective, not a
scientifically demonstrated gap. The critical objection “is this merely
provenance plus an existing memory policy?” remains unresolved, so the decision
must be `no_go` under the project rule.

## Baselines, metrics, and resource implication

If this direction is ever reopened, the minimum baselines are `no_memory`,
`vector_retrieval`, `summary_memory`, and `source-aware retrieval without
consolidation`. Metrics must include `long_horizon_success`,
`unsupported_claim_rate`, `source_attribution_accuracy`, memory size, and
token/latency cost. These are feasibility requirements, not evidence that the
method is novel.

The OpenAlex phase has an estimated usage profile: `phase=literature`,
`measurement_status=estimated`, `tool_calls=4`, `retry_count=0`,
`wall_time_ms=10522`, and null input/output tokens. Manual PDF inspection used
no model calls and has no token record.

## Final routing

`memory_engine` is abandoned as the current paper direction. It must not enter
Method Design, drafting, Publication Gate, or Stanford Reviewer. The next
research-value review should switch to `context_engineering` or
`self_evolution`, with the same requirement that an independent mechanism be
shown against closest prior work before implementation effort begins.
