# IQ Non-Parametric Learning

Combining the **Microsoft IQ stack** (Fabric IQ Ontology + Foundry) for enterprise context with
**non-parametric learning** (frozen model weights; optimize the harness, prompts, tools, and skills)
to optimize an agent, tap into **model independence / frontier-model swappability**, and keep the
semantic layer as a durable **semantic contract**.

> **Status:** Early-stage. Private while under construction. This repo backs a forthcoming public
> article. Nothing here is verified for production use yet.

## The two headline ideas
- **Fabric IQ = the semantic contract.** Data structure and business vocabulary live in the ontology,
  not in prompts. The agent reasons across streams, lab data, and assets via graph traversal — no SQL.
- **Model swappability.** Because the ontology owns the schema, the model becomes a swappable commodity:
  change it via config, not code, and prove a smaller optimized model can match a flagship.

## Scenario
Water utilities responding to **algal blooms** (cyanobacteria; MIB/Geosmin taste-and-odor compounds;
cyanotoxins) across sensor/telemetry, lab, and asset/geospatial data.

## Governance
This project is governed by [`CONSTITUTION.md`](./CONSTITUTION.md). Key hard rules:
- All technical claims are verified against primary Microsoft sources before publication.
- Model weights are never altered — optimization is text-space only.
- Every change is backed by a GitHub **Epic → Issue → PR**; merges via reviewed PRs only.
- Nothing is made public without explicit approval.

See [`docs/plan.md`](./docs/plan.md) for the phased plan.

## License
Code: MIT (see [`LICENSE`](./LICENSE)). Prose/article content: CC-BY.
