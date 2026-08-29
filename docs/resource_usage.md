# ResearchUsageRecord

`ResearchUsageRecord` is the common resource protocol for every research
phase, including `value_gate`, `literature`, `method_design`,
`experiment_design`, `drafting`, `internal_review`, and `publication_review`.

`measurement_status` is explicit:

- `observed`: measured from an execution;
- `estimated`: a declared estimate, not an observed value;
- `pending`: not yet available. Numeric fields may be `null` or zero.

Observed records must provide every numeric resource field. Estimated records
may leave unknown fields as `null` when an estimate covers only part of a
request, such as request count and wall time. The implementation never
converts missing values into observed zeroes. Aggregation uses zero only for
pending or unknown numeric values in totals, while the original record retains
its explicit measurement status.

Every artifact path is relative and must contain its `research_run_id`, which
keeps resource reports associated with the research run that produced them.
No model provider, search engine, or reviewer is called by this protocol.
