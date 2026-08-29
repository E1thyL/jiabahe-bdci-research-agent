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

The builder does not decide `go`, `revise`, or `no_go`; the existing
`ResearchValueGate` remains the decision authority.
