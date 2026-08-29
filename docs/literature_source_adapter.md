# LiteratureSourceAdapter

The literature boundary is adapter-first and offline-replayable:

```text
CandidateProblem
  -> LiteratureSourceAdapter.search(candidate, topic_config)
  -> LiteratureSearchResult
  -> EvidenceBundle / EvidenceIndex
  -> ResearchValueGate
```

`ReplayLiteratureSource` is the first implementation. It maps an exact fixture
query to source-owned `LiteratureRecord` values and never performs network I/O.
The adapter materializes `EvidenceItem` values, so the model does not invent
evidence directly. `source_hash` is a SHA-256 hash over canonical JSON of the
source URI, metadata, excerpt, evidence type, and verification status. The
derived evidence ID is the source name plus the first 16 hash characters.

Search status is explicit: `success`, `empty`, `partial`, or `failed`.
Failures retain a reason and produce no verified evidence. Empty results are
not failures and do not automatically produce `no_go`; the Value Gate decides
based on the resulting evidence and candidate fields.

The collector accepts an optional `UsageSink`. Replay collection has no real
model or network measurement, so its default usage record is
`measurement_status=pending` with phase `literature`.
