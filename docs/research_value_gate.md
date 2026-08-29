# Research Value Gate

The gate is an early research-quality checkpoint, not a paper conclusion.

```text
CandidateProblem
  -> Scope / Significance Pre-Gate
  -> EvidenceCollector
  -> Evidence-backed Research Value Gate
  -> Method Design
  -> Experiment Design
  -> Publication Gate
  -> Draft
```

This first implementation is deterministic and offline. Callers provide
`EvidenceItem` records; the module does not search the web or call a reviewer.
Novelty requires a closest prior work, an explicit gap and difference, and
verified literature evidence. Before experiments run, experiment status is
`pending`; a `go` decision means only that method and experiment design may
proceed. It does not mean the hypothesis has been experimentally proven.

The supported topic policies are `context_engineering`, `memory_engine`, and
`self_evolution`. They provide review criteria, baseline expectations, and
metric expectations without hard-coding one research theme into the gate.
