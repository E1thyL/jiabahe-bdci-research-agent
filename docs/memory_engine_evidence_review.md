# Memory-engine evidence review

Run: `memory-evidence-review-20260829`  
Candidate: **Provenance-aware selective memory consolidation for long-horizon
Agent research tasks**  
Source: OpenAlex Works API, one page per query  
Review date: 2026-08-29

This is a controlled evidence review, not a final paper-topic approval. The
adapter's `verified` status means that an OpenAlex record was normalized with a
non-empty URI, title, excerpt, and stable provenance hash. It does **not** mean
that the paper's technical claims or the proposed novelty have been verified
from full text. Abstract-only technical interpretation is therefore marked
`pending` below.

## Candidate and review questions

The working hypothesis is that source-aware selective consolidation improves
long-horizon research-task success while reducing unsupported remembered
claims. The review asks:

1. What do current agent-memory systems actually optimize: long context,
   retrieval, episodic experience, task planning, or continual learning?
2. Is source attribution in agent memory already a complete research line?
3. Is “selective consolidation” a distinct mechanism, or only a new name for
   memory-write and update policies?
4. Which baselines and metrics can distinguish source-aware consolidation from
   ordinary vector retrieval or summary memory?

## Bounded retrieval

The six exact queries were:

```text
LLM agent memory long horizon
episodic semantic memory for agents
memory consolidation language model agents
provenance attribution memory agents
continual memory update autonomous agents
research task memory retrieval
```

All six calls used `timeout=10s`, `max_pages=1`, and `max_retries=1`. Each
returned `partial`; counts were 24, 20, 21, 24, 21, and 17 normalized records
respectively. The total is 127 records before cross-query deduplication. The
raw snapshots are ignored local artifacts at:

```text
.pilot-cache/memory-evidence-review-20260829/openalex-47d826417289c87c.json
.pilot-cache/memory-evidence-review-20260829/openalex-728d78a14960de7a.json
.pilot-cache/memory-evidence-review-20260829/openalex-f10ed92be372f618.json
.pilot-cache/memory-evidence-review-20260829/openalex-34426f4dadb82d32.json
.pilot-cache/memory-evidence-review-20260829/openalex-8a1427bc05c5e901.json
.pilot-cache/memory-evidence-review-20260829/openalex-d881f123b52a3554.json
```

The last query was especially noisy, returning mostly general human-memory
literature rather than research-agent systems. This is a retrieval limitation,
not evidence that the candidate has no prior work.

## Closest-prior-work shortlist

The table is an auditable shortlist, not an assertion that every item is
equally close. All IDs, hashes, URIs, titles, years, venues, and excerpts are
copied from the OpenAlex-normalized records. `source verified / science
pending` means provenance is complete but the abstract or metadata is not
enough to establish the detailed technical comparison.

| paper | authors | year / venue | evidence ID | source URI | source hash | memory representation / write-update / retrieval / forgetting / provenance / evaluation | limitation and relation to candidate |
|---|---|---|---|---|---|---|---|
| A survey on large language model based autonomous agents | Lei Wang; Chen Ma; Xueyang Feng | 2024, Frontiers of Computer Science | `openalex:f33a77fa7ff303d1` | https://doi.org/10.1007/s11704-024-40231-1 | `f33a77fa7ff303d1594fa4069e94559948ac132b92b13362f7a97c64026b5b21` | Survey-level taxonomy; detailed policy and provenance not established in excerpt | Maps the space but is not a competing consolidation method; science pending |
| Meta-Cognitive Memory Policy Optimization for Long-Horizon LLM Agents | Ziyan Liu; Zhezheng Hao; Yeqiu Chen | 2026, arXiv | `openalex:8f2d367c9d2394a0` | https://doi.org/10.48550/arxiv.2605.30159 | `8f2d367c9d2394a0804b05ed1ebfec905c2a14f4811bcba05afca5d193cbfa44` | Recursive compact memory and learned memory policy; retrieval and provenance details require full text | Directly challenges “selective consolidation” as distinct novelty. Full comparison pending |
| Memory Matters: The Need to Improve Long-Term Memory in LLM-Agents | Kostas Hatalis; Despina Christou; J. Myers | 2024, Proceedings of the AAAI Symposium Series | `openalex:e90466613ccd9d2f` | https://doi.org/10.1609/aaaiss.v2i1.27688 | `e90466613ccd9d2f0943273750bfb83483186c9f9ae6c20a7f3ca34cf46e35f7` | Review of memory management for LLM agents; policy and provenance are not recoverable from the excerpt | Supports significance, not a novelty gap; science pending |
| HiAgent: Hierarchical Working Memory Management for Solving Long-Horizon Agent Tasks with Large Language Model | Mengkang Hu; Tianxing Chen; Qiguang Chen | 2025, ACL Long Papers | `openalex:6a99beb3f585ff83` | https://doi.org/10.18653/v1/2025.acl-long.1575 | `6a99beb3f585ff8344ed010a77681b0eb2eb94ef758f74c302c41950443d43a1` | Hierarchical working memory for long-horizon tasks; exact writes, retrieval, forgetting and provenance need full text | Strong baseline candidate; candidate must show more than hierarchy or compression |
| Generative Agents: Interactive Simulacra of Human Behavior | Joon Sung Park; Joseph O'Brien; Carrie J. Cai | 2023, venue absent in normalized record | `openalex:db776f088fd65c44` | https://doi.org/10.1145/3586183.3606763 | `db776f088fd65c446c6d1a6a42298ae71cc3d3e261b4f1b91d2e99813024958f` | Experience memory and reflection for believable agents; provenance handling is not established here | Relevant episodic-memory baseline, but task domain differs |
| Semantic Memory Modeling and Memory Interaction in Learning Agents | Wenwen Wang; Ah-Hwee Tan; Loo-Nin Teow | 2016, IEEE TSMC Systems | `openalex:782cee3f10c903f5` | https://doi.org/10.1109/tsmc.2016.2531683 | `782cee3f10c903f58d785a290538d9de6648cf74f242e37a6db96cb19fe840b6` | Semantic memory abstraction and interaction in learning agents; not an LLM research-task setting | Establishes older semantic-memory prior; candidate needs a concrete cross-setting difference |
| Data Provenance for Multi-Agent Models in a Distributed Memory | D.T. Davis | 2017, University of Washington ResearchWorks | `openalex:468ccacc948c31da` | http://hdl.handle.net/1773/40436 | `468ccacc948c31dacc790d1abb5eaa32364dd3e3990ac75f45003720f4498579` | Title indicates distributed-memory provenance; normalized excerpt is thesis metadata only | Directly warns that provenance-aware memory is not automatically new; technical comparison pending |
| Chronology of multi-agent interactions for provenance of evolving information | Ching-Chun Chang; Isao Echizen | 2026, Royal Society Open Science | `openalex:a5c75c4bde4ffa6b` | https://doi.org/10.1098/rsos.251988 | `a5c75c4bde4ffa6bd9904ad6c011a545f9aed01e327fe09a954aabe440220cf2` | Chronological provenance for evolving multi-agent information; memory update and retrieval mechanism require full text | Relevant provenance prior; candidate must specify an agent-memory mechanism and evaluation beyond chronology |
| Gradient Episodic Memory for Continual Learning | David López-Paz; Marc’Aurelio Ranzato | 2017, arXiv | `openalex:bb2a022c384d5f5b` | http://arxiv.org/abs/1706.08840 | `bb2a022c384d5f5b30c1dea5acee83fab5b6110294073749c3b023cd32d8d7c2` | Episodic replay for continual learning; not an LLM agent memory system | Useful conceptual baseline for forgetting/interference, but not direct evidence for the proposed gap |

This item is not used as a Gate citation because it is a conceptual continual-
learning prior rather than a close LLM-agent memory work. It remains a useful
search lead and baseline for forgetting/interference. The general rule still
holds: a paper without a complete EvidenceItem must not support a Gate
decision.

## Prior-work clusters and gap assessment

The evidence forms four clusters:

1. **Long-horizon working/episodic memory:** HiAgent, Generative Agents, and
   the LLM-agent survey address memory capacity, organization, or experience.
2. **Learned memory write/update policy:** Meta-Cognitive Memory Policy
   Optimization is especially close and may already cover selective policy
   learning under long-horizon tasks.
3. **Semantic and continual memory:** Semantic Memory Modeling and Learning
   Agents plus Gradient Episodic Memory provide older representations and
   forgetting/interference priors.
4. **Provenance:** Data Provenance for Multi-Agent Models and Chronology of
   Multi-Agent Interactions show that source/history tracking is not an
   untouched concept.

The supported statement is narrow: long-horizon agent memory and provenance
are both established concerns, while this six-query snapshot does not provide
enough full-text evidence to establish whether *source-aware selective
consolidation for research tasks* is a distinct contribution. The novelty gap
is therefore `insufficient`, not `supported`. In particular, “selective
consolidation” may be a relabeling of memory-write/update policies; that must
be resolved by reading the closest papers' algorithms and ablations.

## Baseline and metric plan

The minimum discriminating baseline set is:

| baseline | purpose |
|---|---|
| no memory | measures whether memory helps at all |
| vector retrieval | tests ordinary similarity retrieval |
| summary memory | tests lossy consolidation without source-aware selection |
| source-aware retrieval without consolidation | isolates provenance from write/update policy |
| proposed selective consolidation | tests the actual hypothesis |

Required metrics are `long_horizon_success`, `memory_precision`,
`unsupported_claim_rate`, and `source_attribution_accuracy`; secondary metrics
should include memory size, retrieval latency, and token cost. These are
executable plans, not experimental results.

## Decision

```json
{
  "mechanical_gate_decision": "go",
  "scientific_review_decision": "revise",
  "status": "insufficient",
  "reason": [
    "OpenAlex recall remains noisy under the six bounded queries",
    "the closest work's algorithms and ablations have not been full-text verified",
    "provenance-aware memory may already have direct multi-agent precedents",
    "selective consolidation may be terminology for existing memory-write policies"
  ]
}
```

The candidate must not enter Method Design yet. A scientific `go` requires a
manually verified closest-work comparison, an evidence-bound gap, at least two
executable baselines, at least two quantitative metrics, and no unresolved
critical objection. If full-text review shows that the combination is already
covered, the correct result is `no_go`, not a forced narrowing that preserves
the topic name.

## Usage and provenance

The run made 6 HTTP calls, with 0 retries and approximately 13,555 ms wall
time. No token counts were available. The appropriate usage record is
`phase=literature`, `measurement_status=estimated`, `tool_calls=6`,
`retry_count=0`, `wall_time_ms=13555`, and null input/output tokens. No
`observed + 0` token record was created. No additional usage record is claimed
for manual review because it involved no model call.

No real source adapter, JiuwenSwarm, agent-core, Publication Gate, Stanford
Reviewer, or research Rail was changed in this review.
