# OpenAlex Literature Adapter

`OpenAlexLiteratureSource` is the first real source adapter. It implements the
common `LiteratureSourceAdapter.search(candidate, topic_config)` contract and
uses only the public OpenAlex Works endpoint. The transport is injectable, so
tests use fixed responses and never access the network.

Each request is bounded by a timeout, retry limit, page limit, and OpenAlex
`per-page` limit. HTTP 429 and 5xx responses are retried; other HTTP errors,
timeouts, malformed JSON, and invalid response shapes become `failed` results.
`empty` means a successful response with no usable records, while `partial`
means some records were discarded because required metadata such as a source
URI or abstract was missing.

The adapter stores a normalized raw-response snapshot under:

```text
<cache_dir>/<research_run_id>/openalex-<query-hash>.json
```

The snapshot is retained alongside the normalized `EvidenceItem` values for
provenance review. A stable SHA-256 hash is calculated from canonical record
metadata, and the evidence ID combines `openalex` with the first 16 hash
characters. A successful HTTP response only establishes source-level
verification: metadata proves that a paper exists, while an abstract excerpt
supports only limited claims. It does not prove the paper's scientific
conclusions.

No API key is stored in the repository. OpenAlex usage records default to
`measurement_status=pending`; callers may provide explicit observed or
estimated statistics through `UsageSink`.
