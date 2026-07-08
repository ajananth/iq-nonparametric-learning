# Baseline comparison scorecard

_Generated 2026-07-08T04:26:29.602668+00:00 · single-variable fairness: only the model deployment string varies; ontology + config + eval set + SQL ground truth are identical._

| Metric | `gpt-5.4` |
| --- | --- |
| Accuracy overall % | 91.7 |
|   single_hop % | 87.5 |
|   multi_hop % | 90.0 |
|   negative % | 100.0 |
| Tokens total | 107450 |
| Tokens avg/task | 4477.1 |
| Cost total (USD) | 0.17535 |
| Cost/correct (USD) | 0.00797 |
| Latency avg (ms) | 30002 |
| Grounded % | 100.0 |
| Multi-hop traversal % | 90.0 |
| Config hash | 0646fb478d95 |

## Fairness / frozen-weights control

- Identical config across models: **True** (single shared config hash).
- Fine-tuning: **none** (model is a deployment-name string; weights frozen — Art. II).
- Only variable across runs: the model deployment string (Art. III).
