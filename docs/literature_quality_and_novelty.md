# Literature quality and novelty gap

The offline research chain is:

```text
CandidateProblem
  -> OpenAlex / Replay LiteratureSource
  -> EvidenceBundle
  -> LiteratureQualityFilter
  -> NoveltyGapBuilder
  -> ResearchValueGate
```

`LiteratureQualityFilter` checks URI, title, excerpt, source hash, evidence ID
shape, verification status, year, and venue. Missing year or venue is reported
as a limitation rather than converted to `no_go`. Search `failed`, `empty`, and
`partial` states remain distinguishable from record-level incompleteness.

`NoveltyGapBuilder` only accepts evidence IDs that are present in the bundle,
structurally usable, and `verification_status=verified`. Title or metadata
alone cannot support a technical difference. Abstract/excerpt records support
only a bounded method overview and are explicitly marked as insufficient for a
complete technical-difference claim. Missing or pending prior work produces an
`insufficient` or `pending` gap, never a fabricated novelty claim.

## Decision semantics

`verification_status=verified` means that the evidence provenance can be
audited; it does not mean that every scientific claim in the source is
verified. `support_level=metadata` or `support_level=abstract` can establish
that a relevant precedent exists and can support a bounded method overview,
but cannot establish a complete technical difference or novelty gap. A
technical-difference claim therefore requires corresponding `full_text`
evidence. When that evidence is unavailable, the builder returns
`insufficient` (or `pending` for a partial or failed source) and clears
`supported_gap` and `candidate_difference`.

The mechanical `ResearchValueGate` decision is a separate screening result:
`mechanical_gate_decision=go` is not a novelty conclusion. The pilot's
`scientific_review_decision` fails closed to `revise` whenever the novelty
status is not `supported` or any unsupported claim remains. A candidate with a
scientific decision of `revise` must not enter Method Design.

The builder does not decide `go`, `revise`, or `no_go`; the existing
`ResearchValueGate` remains the decision authority.
