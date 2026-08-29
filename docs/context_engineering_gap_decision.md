# Context-engineering final gap decision

Run: `context-gap-decision-20260829`  
Candidate: **Evidence-preserving context compaction and routing for
long-horizon multi-agent research tasks under token budgets**  
Date: 2026-08-29

## Decision

```ini
context_engineering = no_go
method_design = not_allowed
```

The candidate combines four established ingredients: context compression,
multi-agent communication, long-context evaluation, and token accounting. The
review did not find a distinct evidence-preserving context-selection or routing
algorithm for multi-agent research tasks. Adding provenance metadata or placing
the ingredients in one pipeline would be engineering composition, not a
defensible paper contribution.

## Candidate

Working problem: can evidence-preserving compaction and routing improve
long-horizon multi-agent research tasks under a fixed token budget?

Working hypothesis: a context policy that preserves task-critical evidence and
routes only relevant context improves task success and evidence retention while
reducing input-token cost and contamination.

This is testable with `full_context`, `summary_only`, and ordinary retrieval
baselines, but the mechanism is not novel. Existing compression plus source_id
fields, multi-agent messaging plus provenance metadata, or a long-context
benchmark plus budget reporting are not sufficient differences.

## Controlled retrieval

Queries:

```text
context compression long-horizon LLM agents
multi-agent context sharing or coordination
evidence-preserving context management
token-efficient agent context routing
```

Each query used one page, a 10-second timeout, and at most one retry. Results
were 25 `success`, 17 `partial`, 20 `partial`, and 22 `partial` normalized
records. Raw snapshots are local ignored artifacts under
`.pilot-cache/context-gap-decision-20260829/`.

The evidence-preserving query returned medical guidelines and unrelated uses of
“preservation”. The multi-agent query returned classic coordination and
multi-robot work rather than language-agent context routing.

## Full-text verification

### ACON

Paper: *ACON: Optimizing Context Compression for Long-horizon LLM Agents*  
Evidence ID: `openalex:cd436677fa88b073`  
Source URI: `https://arxiv.org/abs/2510.00615`  
Full-text URI: `https://arxiv.org/pdf/2510.00615`  
Source hash: `cd436677fa88b073ecdb515988bfbff952abc7deb2fb9f71ad4988b96e53509d`

`source_verified=true`; `scientifically_verified=true` for these limited claims:

- Abstract, p. 1: ACON addresses unbounded context growth in long-horizon
  agentic tasks and compresses observations and history.
- Sections 2-3, pp. 2-5: it uses observation/history compressors,
  thresholded compression, and failure-driven optimization of compression
  guidelines. This is an algorithmic compression mechanism.
- Tables 1-2, pp. 6-7: AppWorld, OfficeBench, and 8-objective QA report
  accuracy, steps, peak input tokens, and dependency.
- Table 4, p. 9: API cost and latency are measured for no compression and ACON
  variants, directly overlapping the proposed budget trade-off.
- Section A, p. 16: empirical generalization to other foundation models remains
  limited. This is a limitation, not evidence of research-evidence novelty.

ACON uses single-agent application tasks in the inspected experiments. No
source attribution or evidence-retention metric was found. That leaves a
possible domain adaptation question, not a demonstrated new algorithm.

### CAMEL

Paper: *CAMEL: Communicative Agents for “Mind” Exploration of Large Language
Model Society*  
Evidence ID: `openalex:fd919dc439d872fb`  
Source URI: `http://arxiv.org/abs/2303.17760`  
Full-text URI: `https://arxiv.org/pdf/2303.17760`  
Source hash: `fd919dc439d872fbbf162c8afba586be69e55ba8bb9721a057f7f946de78627c`

`source_verified=true`; `scientifically_verified=true` for these limited claims:

- Abstract and pp. 2-3: CAMEL studies autonomous cooperation among
  communicative agents using role-playing and inception prompting.
- Sections 3-4, pp. 4-8: an AI user plans and an AI assistant executes through
  role-specific messages; role flipping, repeated instructions, flaky replies,
  and infinite message loops are documented failure modes.
- Section 4.2, p. 9: summarized agent solutions are compared with a
  single-shot GPT-3.5 solution using human evaluation.

CAMEL does not provide the candidate's evidence-preserving selection rule and
does not establish long-horizon research-task evaluation. Multi-agent context
sharing cannot be claimed as new by itself.

### Gemini 1.5

Paper: *Gemini 1.5: Unlocking multimodal understanding across millions of
tokens of context*  
Evidence ID: `openalex:58b23066383cca9f`  
Source URI: `http://arxiv.org/abs/2403.05530`  
Full-text URI: `https://arxiv.org/pdf/2403.05530`  
Source hash: `58b23066383cca9f3258399de7100adadcfb6c19c53cb841aec4d8b12e79c43c`

`source_verified=true`; `scientifically_verified=true` for these limited claims:

- Sections 12.11-12.16, pp. 130-150: the report evaluates long-document QA,
  TREC information-seeking tasks, needle-in-a-haystack recall, and
  token-scale contexts.
- Section 12.11, p. 130: Qasper uses full article context and human accuracy
  assessment. This is relevant to evidence-bearing context, but not a
  context-selection algorithm.
- Section 12.16.7, p. 142: needle-in-a-haystack measures retrieval from large
  contexts, not preservation during agent compaction.

Gemini 1.5 is a model and evaluation report, not a multi-agent context router.

## Overlap matrix

`Yes` means supported by full-text inspection. `No` means no support was found
for that dimension in the inspected text.

| dimension | ACON | CAMEL | Gemini 1.5 | candidate |
|---|---|---|---|---|
| context representation | history and observation summaries | role-specific messages | very long multimodal/text context | evidence-bearing routed context |
| compression / selection | Yes, optimized history/observation compression | conversation summarization | no compaction algorithm | evidence-preserving compaction |
| routing mechanism | compressor invocation thresholds | role-based communication | no agent routing | multi-agent evidence-aware routing |
| long-horizon task | Yes, AppWorld and related long tasks | not established | long-context tasks, not agents | Yes |
| multi-agent setting | not established in experiments | Yes | not established | Yes |
| evidence / provenance | No evidence | No evidence | supporting-context evaluation, no provenance tracking | Required |
| budget awareness | peak tokens, dependency, API cost, latency | not established | context-length scaling | token and latency budget |
| baselines | no compression, FIFO, retrieval, LLMLingua, prompting | single-shot solution | GPT-4 Turbo and other model baselines | full context, summary, retrieval |
| metrics | accuracy, steps, peak tokens, dependency, cost, latency | human preference and task evaluation | recall, QA accuracy, helpfulness | success, retention, contamination, tokens, latency |
| failure mode | irrelevant context and degradation | role flipping, loops, flaky messages | large-context retrieval limits | evidence loss, contamination, unsupported claims |

## Real gap and decision rationale

The only plausible remaining question is whether an evidence-aware context policy
can improve research-task evidence retention and unsupported-claim rate under a
fixed budget. The review does **not** establish that this requires a new
algorithm. ACON already supplies adaptive compression, failure-driven
optimization, and cost/quality measurement; CAMEL supplies multi-agent
communication failure modes; Gemini supplies large-context evaluation.

A future proposal would need a genuinely new selection/preservation algorithm
that jointly optimizes evidence utility, cross-agent contamination, and future
task value, with ablations showing it is not equivalent to ACON, retrieval, or
summarization. No such mechanism was found here. The feasible baselines are
`full_context`, `summary_only`, FIFO/retrieval compression, and a multi-agent
routing baseline. Candidate metrics are evidence retention rate, unsupported
claim rate, context contamination rate, long-horizon task success, input token
cost, and latency. These satisfy feasibility but do not cure the novelty
objection.

## Resource record

The OpenAlex phase made 4 HTTP requests, used 0 retries, and took approximately
12,228 ms. No token counts were available. The correct semantics are:

```ini
phase = literature
measurement_status = estimated
tool_calls = 4
retry_count = 0
wall_time_ms = 12228
input_tokens = None
output_tokens = None
```

No model or reviewer call was made. Snapshots contain the run ID and remain
ignored local artifacts.

## Final routing

`context_engineering=no_go`. It must not enter Method Design, drafting,
Publication Gate, or Stanford Reviewer. The next candidate review should move
to `self_evolution`, with the same requirement that an independent mechanism
and full-text-supported gap be shown before implementation.
