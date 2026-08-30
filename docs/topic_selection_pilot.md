# Three-direction literature value-screening pilot

Run: `topic-pilot-20260829`  
Source: OpenAlex Works API  
Date: 2026-08-29  
Mode: bounded live retrieval with local snapshots

This pilot is evidence collection, not a claim that any candidate is ready for
publication. Each direction used three queries, one page per query, a 10-second
timeout, and at most one retry. The nine raw responses are kept locally under
`.pilot-cache/topic-pilot-20260829/`; the directory is ignored and is not part
of the GitHub commit.

## Important interpretation boundary

The existing `ResearchValueGate` treats an OpenAlex-normalized item as
`verified` when the source record has an accessible URI, title, abstract
excerpt, and stable hash. That is provenance verification, not scientific
verification of every claim in the paper. The pilot therefore reports the
mechanical Gate result separately from the research decision.

The current queries are too broad for a defensible novelty claim. Several
results are clearly off-topic, and some OpenAlex abstract fields contain only
author or proceedings metadata. Consequently, the pilot decision for all
three directions is **revise**, even where the unchanged rule engine returns
`go` after all returned IDs are attached. No candidate is promoted to method
design on this pilot alone.

## Retrieval summary

| direction | queries | result status / records | normalized records | quality result | mechanical Gate | pilot decision |
|---|---:|---|---:|---|---|---|
| `context_engineering` | 3 | partial 19, success 25, partial 20 | 63 | 63 usable; recall is noisy | `go` | `revise` |
| `memory_engine` | 3 | success 25, partial 22, success 25 | 71 | 71 usable; recall is noisy | `go` | `revise` |
| `self_evolution` | 3 | partial 24, success 25, partial 24 | 72 | 72 usable; recall is noisy | `go` | `revise` |

`partial` means OpenAlex returned records but at least one record could not be
normalized, normally because a source URI, title, or abstract was absent.
There were no `empty` or HTTP `failed` results in this run. The raw response is
still the authority for auditing these counts.

## Candidate A: context engineering

Candidate problem: “Can evidence-preserving context compression improve
multi-agent research tasks under a fixed token budget?”

Hypothesis: evidence-preserving compression improves task quality and evidence
retention at lower token cost.

Planned contribution: an evidence-retention evaluation protocol for compressed
multi-agent research context. Baselines are `full_context` and
`summary_only`; proposed metrics are `task_quality`, `evidence_retention`, and
`token_cost`.

The strongest retrieved anchors were:

| evidence ID | title | year | source URI |
|---|---|---:|---|
| `openalex:b5fbf93da4acc2fa` | LongLLMLingua: Accelerating and Enhancing LLMs in Long Context Scenarios via Prompt Compression | 2024 | https://doi.org/10.18653/v1/2024.acl-long.91 |
| `openalex:3f8832910dc6ad85` | MemGPT: Towards LLMs as Operating Systems | 2023 | http://arxiv.org/abs/2310.08560 |
| `openalex:a6efd54e214ecd87` | Do Cross-References Help LLM Agents Complete Documents? | 2026 | https://mcp-data-platform.txn2.com/reference/benchmark-report-graph-completion/ |

For example, the LongLLMLingua item has source hash
`b5fbf93da4acc2fab13580984ea7438cb7316217f408f69d04215ac375195124`.
Its normalized excerpt is not a reliable technical abstract in this snapshot,
so it proves record provenance but not the claimed method details. The first
query also returned unrelated preservation papers. The resulting gap is a
candidate gap only, not evidence-backed novelty. In this historical run the
structural builder reported `supported`, while the scientific interpretation
was `insufficient`; the fail-closed builder now reports `insufficient` for the
same abstract-only evidence. The pilot decision remains `revise`.

## Candidate B: memory engine

Candidate problem: “Can source-aware selective memory consolidation improve
long-horizon research tasks?”

Hypothesis: source-aware selective consolidation improves long-horizon success
while reducing unsupported remembered claims.

Planned contribution: a source-aware memory-consolidation benchmark. Baselines
are `vector_retrieval`, `summary_memory`, and `no_memory`; metrics are
`long_horizon_success`, `memory_precision`, and `unsupported_claim_rate`.

Relevant anchors included:

| evidence ID | title | year | source URI |
|---|---|---:|---|
| `openalex:a1e447b1871fd54d` | Reflexion: Language Agents with Verbal Reinforcement Learning | 2023 | http://arxiv.org/abs/2303.11366 |
| `openalex:41f753e47ff9dfa2` | ExpeL: LLM Agents Are Experiential Learners | 2024 | https://doi.org/10.1609/aaai.v38i17.29936 |
| `openalex:38586fd1d7c5bd37` | Evaluating Very Long-Term Conversational Memory of LLM Agents | 2024 | https://doi.org/10.18653/v1/2024.acl-long.747 |

The corresponding source hashes are, respectively,
`a1e447b1871fd54d0c4bdeec6e100b45590d4e12422ae471fdcf4eb02934a846`,
`41f753e47ff9dfa264ea1c7f1c6e1bce186c24da80c70ba08366ed344ab5af42`, and
`38586fd1d7c5bd37d9c33a49a449276ba73a10e95181ff286473b3ec58bc326b`.
The first query also returned biomedical and cultural-memory results, showing
that “memory” and “provenance” need field- or concept-constrained retrieval.
This is the most experimentally concrete candidate, but its novelty gap is
not yet defensible from this one-source, noisy snapshot. Status:
`insufficient` for publication; pilot decision: `revise`.

## Candidate C: self evolution

Candidate problem: “Can review-gated reversible Skill updates improve agent
capability without propagating unsafe changes?”

Hypothesis: review-gated reversible updates improve capability while reducing
unsafe Skill propagation.

Planned contribution: a review-gated reversible update protocol. Baselines are
`static_skill_set` and `no_evolution`; metrics are `capability_gain`,
`regression_rate`, and `unsafe_propagation_rate`.

The most useful anchors were:

| evidence ID | title | year | source URI |
|---|---|---:|---|
| `openalex:ecd9b400bc5f8c7e` | ChatDev: Communicative Agents for Software Development | 2024 | https://doi.org/10.18653/v1/2024.acl-long.810 |
| `openalex:fdb8195d82582842` | CHAINIAC: Proactive Software-Update Transparency via Collectively Signed Skipchains and Verified Builds | 2017 | http://infoscience.epfl.ch/record/229405 |
| `openalex:05ccad8fe0e0bf20` | Applicability-First Evaluation Module 03: Update-Rule Admissibility... | 2026 | https://doi.org/10.5281/zenodo.19616417 |

The CHAINIAC source hash is
`fdb8195d82582842ee6d078e4664981e083171d695012bc13fb581eb936be00f`.
The search also returned generic agent surveys, mobile-agent security, and
unrelated policy-update material. The candidate therefore has interesting
systems risk questions but no verified, topic-specific novelty gap from this
pilot. Status: `insufficient`; pilot decision: `revise`.

## Provenance and usage

Every normalized item is created from an OpenAlex adapter record, not from
model text. The adapter derives `source_uri` from the landing page, DOI, or
OpenAlex ID; reconstructs an abstract from `abstract_inverted_index`; and
hashes the canonical tuple of URI, title, authors, year, venue, excerpt,
evidence type, and verification status with SHA-256. The first 16 hex digits
form the stable `evidence_id` suffix. Missing URI, title, or excerpt causes
the record to be excluded or the search to be `partial`; it cannot become
verified evidence.

The live run made nine bounded HTTP requests, one per query, with no observed
retry required. Token counts were unavailable, so the correct usage status is
`estimated`, with `input_tokens = null`, `output_tokens = null`,
`tool_calls = 9`, and no `observed + 0` token claim. The raw snapshot paths
contain `topic-pilot-20260829`. The transient runner did not persist a
per-topic wall-clock usage record, so wall time remains an explicitly missing
measurement rather than fabricated data. This is a follow-up integration gap.

## Decision and next step

No direction is accepted as a final paper topic. If one must be prioritized for
the next controlled study, choose `memory_engine` provisionally because its
long-horizon and unsupported-claim metrics are easiest to operationalize, but
first rerun with a relevance-constrained query set and manually verify the
closest prior works. The next gate should require source-level abstract
evidence for each claimed gap and a deduplicated, human-auditable shortlist.

This pilot does not enter Method Design, Publication Gate, Stanford Agentic
Reviewer, or any Rail implementation.
