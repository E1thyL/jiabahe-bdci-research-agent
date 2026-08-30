# Context-engineering multi-resolution candidate review

Run: `context-multires-review-20260830`  
Baseline: `main@366a2b8650ea2f77e6c22e76af76f5bbcb69d279`  
Scope: independent Agent/CS literature review only. No DeepSeek, drafting,
Method Design, experiments, or Stanford Reviewer calls were made.

## Candidate under review

The candidate proposes per-segment verbatim, entity/triple, summary, and
cluster representations; a next-decision utility router chooses the
granularity under a token budget; episodic bandit feedback trains the router;
and long-horizon agent task success and token efficiency are evaluated.

## Controlled OpenAlex retrieval

Every query used one page and at most one retry. `request_count`,
`retry_count`, `wall_time_ms`, and the exact query are retained in
`.pilot-cache/context-multires-review-20260830/context_engineering_review.json`.
Each snapshot is source-owned and run-scoped.

| query | status / normalized records | usage | snapshot |
|---|---|---|---|
| `multi-resolution context representation LLM agents` | success / 25 | 1 request, 0 retries, 2405 ms | `.pilot-cache/context-multires-review-20260830/openalex-def0ec61dffdf9cf.json` |
| `adaptive context abstraction selection long-horizon agents` | partial / 17 | 1, 0, 1969 ms | `.pilot-cache/context-multires-review-20260830/openalex-a4dab55682921c1e.json` |
| `token budget utility-aware context selection agents` | partial / 22 | 1, 0, 1905 ms | `.pilot-cache/context-multires-review-20260830/openalex-f79885f106575405.json` |
| `bandit reinforcement learning context compression agents` | partial / 22 | 1, 0, 2061 ms | `.pilot-cache/context-multires-review-20260830/openalex-fb1c060a9f0a92df.json` |
| `memory augmented long-horizon LLM agents context compression` | partial / 24 | 1, 0, 1938 ms | `.pilot-cache/context-multires-review-20260830/openalex-da7d5bb855241b97.json` |
| `MemGPT virtual context management` | success / 25 | 1, 0, 1655 ms | `.pilot-cache/context-multires-review-20260830/openalex-4c686c45e8573df6.json` |

Total: 6 OpenAlex requests, 0 retries, approximately 11,933 ms. The
automated `LiteratureQualityFilter` marks the normalized records as
provenance-usable but `support_level=abstract`. `NoveltyGapBuilder` therefore
returns `insufficient` for the success queries and `pending` for partial
queries; it does not treat these snapshots as full-text novelty evidence.

## Full-text verification

The following public PDFs were downloaded once and inspected locally. Page
numbers below refer to the downloaded PDFs. The extracted notes are retained
in `.pilot-cache/context-multires-review-20260830/fulltext_verification.json`;
the PDFs themselves are ignored run artifacts.

### R3Mem

OpenAlex: `W4412888700`; evidence ID: `openalex:42d5b8d45008fdd8`  
Full text: <https://aclanthology.org/2025.findings-acl.235.pdf>

- pp. 1-4 (abstract, introduction, architecture): reversible context
  compression with virtual memory tokens and explicit document/paragraph/
  sentence/entity hierarchical compression.
- pp. 6-8 (retrieval, evaluation, ablations): long-context and conversational
  long-horizon evaluation, retrieval F1/response correctness/coherence/ranking
  and latency; ablations show hierarchical context-query pairs matter.
- The training objective is forward/backward likelihood plus cycle consistency,
  not an episodic bandit or future-utility selector. No fixed token-budget
  utility policy is established.

### ACON

OpenAlex: `W4414808569`; evidence ID: `openalex:cd436677fa88b073`  
Full text: <https://arxiv.org/pdf/2510.00615>

- pp. 1-5 (abstract and Sections 3.1-3.3): long-horizon agent context cost,
  history/observation compression, compression thresholds, and failure-driven
  guideline optimization.
- pp. 6-9 (Tables 1-3 and ablations): AppWorld, OfficeBench and
  Multi-objective QA; task accuracy, steps, peak tokens, dependency, API cost
  and latency. The optimizer uses contrastive/failure feedback and is not a
  bandit policy-gradient router.
- The paper does not establish per-segment verbatim/entity/triple/summary/
  cluster representations or an explicit expected-future-utility selector.

### MemGPT

OpenAlex: `W4387636003`; evidence ID: `openalex:3f8832910dc6ad85`  
Full text: <https://arxiv.org/pdf/2310.08560>

- pp. 1-4 (abstract, Sections 1-2.4): virtual context management, working/FIFO,
  recall and archival memory tiers, queue eviction at a context warning
  threshold, and function-based retrieval.
- pp. 5-8 (Sections 3.1-3.2 and figures): multi-session chat, document QA and
  nested key-value long-context evaluation with accuracy/ROUGE-L/CSIM metrics.
- The control flow is event/function based; no learned bandit/RL utility router
  or explicit budget optimization objective is established.

## Overlap matrix

`Yes` means directly supported by the inspected full text. `Partial` means a
related mechanism or metric is present but not the candidate's exact claim.

| dimension | R3Mem | ACON | MemGPT | candidate |
|---|---|---|---|---|
| representation hierarchy | Yes: document/paragraph/sentence/entity and virtual tokens | Partial: compressed history/observations, no stated hierarchy | Yes: working/FIFO/recall/archival tiers | verbatim/entity-triple/summary/cluster per segment |
| context selection | adaptive retrieval/reconstruction | thresholds and optimized compression guidelines | eviction plus function retrieval | utility-aware granularity router |
| future utility | not an explicit objective | task reward/failure feedback for compression | not a learned future-utility objective | expected next-decision utility |
| token budget | compression and latency reported, no budget selector | cost function, peak-token and API-cost trade-offs | finite-window warning threshold | fixed-budget context composition |
| bandit/RL optimization | no; likelihood/backward/cycle losses | no bandit; failure-driven guideline optimization | no bandit/RL update | episodic bandit feedback |
| long-horizon agent | conversational-agent interaction tasks | AppWorld/OfficeBench/Multi-objective QA | multi-session and long-document agents | long-horizon research agents |
| evaluation metrics | perplexity, retrieval F1, correctness/coherence, ranking, latency | accuracy, steps, peak tokens, dependency, cost, latency | accuracy/ROUGE-L, CSIM, nested-KV accuracy | success and token efficiency |
| failure modes | out-of-domain generalization and memory integration instability | irrelevant context, lost state, incorrect summary, compression overhead | overflow, truncation degradation, retrieval limits | evidence loss, contamination, router error |

## Decision

The mechanical screening result for a bundle containing the three closest
works is `go`, because the records are provenance-verified and the candidate
fields are populated. This is not a scientific novelty conclusion. The
automated novelty result is `insufficient` because OpenAlex records are
abstract-level and cannot support a complete technical difference.

The independent scientific review is **`no_go`**. R3Mem already covers
multi-granularity context compression and long-horizon retrieval; ACON covers
adaptive failure-driven compression with token/cost and long-horizon
evaluation; MemGPT covers hierarchical memory, eviction/retrieval control and
long-context agents. The proposed episodic bandit utility router is not shown
by the inspected evidence to be a distinct mechanism rather than a composition
of established compression, memory and feedback components. Renaming the
combination for research agents would not cure that overlap.

```ini
mechanical_gate_decision = go
scientific_review_decision = no_go
candidate_status = no_go
method_design = false
```

## Unverified boundaries

- No single inspected paper was proven to implement the exact
  verbatim/entity-triple/summary/cluster plus episodic-bandit combination.
- This review did not run experiments or compare implementations, so it makes
  no empirical superiority claim.
- The `no_go` decision is an overlap judgment from the three inspected full
  texts; it does not upgrade abstract-level OpenAlex evidence to scientific
  verification.
