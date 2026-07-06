# Baseline comparison scorecard

_Generated 2026-07-06T06:49:33.982002+00:00 · single-variable fairness: only the model deployment string varies; ontology + config + eval set + SQL ground truth are identical._

| Metric | `gpt-5.4` | `gpt-5.4-mini` |
| --- | --- | --- |
| Accuracy overall % | 29.2 | 25.0 |
|   single_hop % | 12.5 | 0.0 |
|   multi_hop % | 0.0 | 0.0 |
|   negative % | 100.0 | 100.0 |
| Tokens total | 39793 | 40022 |
| Tokens avg/task | 1658.0 | 1667.6 |
| Cost total (USD) | 0.08146 | 0.016274 |
| Cost/correct (USD) | 0.011637 | 0.002712 |
| Latency avg (ms) | 27361 | 26566 |
| Grounded % | 100.0 | 100.0 |
| Multi-hop traversal % | 0.0 | 0.0 |
| Config hash | e03c59ade0bc | e03c59ade0bc |

## Fairness / frozen-weights control

- Identical config across models: **True** (single shared config hash).
- Fine-tuning: **none** (model is a deployment-name string; weights frozen — Art. II).
- Only variable across runs: the model deployment string (Art. III).

## H1 Pareto check (pre-registered)

- Challenger SLM: `gpt-5.4-mini` vs reference LLM: `gpt-5.4`
- Accuracy SLM >= LLM: **False** (25.0% vs 29.2%)
- Tokens ratio SLM/LLM: **1.006** (much-less <= 0.75: False)
- Cost ratio SLM/LLM: **0.2** (much-less <= 0.75: True)
- **Pareto win: False**

> Baseline (un-optimized) figures. H1 is fully tested after Phase 6 optimization; this scorecard pre-registers the criterion and records the starting point.
