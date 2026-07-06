# `eval/` — evaluation framework + baseline scorecards (Phase 5)

> **Issue:** #24 (EPIC D, #4) · **Phase:** 5 (harness + eval + baseline)

**Intent.** A reproducible measurement backbone for the H1 experiment
(`docs/experiment-protocol.md`). It runs the baseline Fabric-IQ-grounded agent (`agent/harness.py`) over a
fixed question set, scores each answer against a **deterministic SQL ground truth** with an **LLM-as-judge**
second opinion, and emits per-task + aggregate scorecards for **both** models — with the ontology grounded
in **all** runs and only the model deployment string varying (single-variable fairness).

## Files
| File | What it is |
| --- | --- |
| `dataset.jsonl` | 24 NL questions: 8 `single_hop`, 10 `multi_hop` (graph traversal), 6 `negative` (unanswerable/out-of-domain -> must fail safe). Each answerable question carries a committed `sql` + `expected_traversal`. |
| `ground_truth.py` | Runs each `sql` over `data/*.csv` with DuckDB and writes `ground_truth.json`. `--check` fails if the committed file is stale. |
| `ground_truth.json` | Committed canonical expected answers (reproducible offline; no Azure). |
| `scorer.py` | Hybrid scorer: drives the harness for one model, scores the six metric families, writes `scorecards/baseline_<model>.{json,md}`. `--dry-run-mock` validates offline. |
| `run_baseline.py` | Runs the matrix over both models, writes `scorecards/baseline_comparison.{json,md}`, and evaluates the pre-registered H1 Pareto criterion. Cost-gated (`--confirm-cost`). |
| `pricing.json` | Per-model token rates for cost math. **Flagged not a verified Microsoft price** (Art. I); only the ratio matters for H1. |
| `eval.yaml`, `eval.jsonl` | Verified **Agent Optimizer** config shapes for Phase 6 (`docs/verified-capabilities.md` §3c). Not used by the Phase-5 scorer. |
| `scorecards/` | Output scorecards (generated; live figures land here after the cost-approved run). |

## Six metric families (per `docs/experiment-protocol.md` §3)
1. **accuracy** — SQL-primary (exact scalar / full-recall set) + LLM-judge (semantic + safe-refusal).
2. **tokens** — input/output per task.
3. **cost** — `$/task` + cost-per-correct-answer (from `pricing.json`).
4. **latency** — wall-clock ms.
5. **grounding** — did it call `fabric_iq_preview`? multi-hop traversal-correctness.
6. **frozen weights** — model deployment string + config hash; `fine_tuning=false`; single shared config.

## Why SQL ground truth is trustworthy (Art. I / Art. V)
The four CSVs in `data/` are vendored **verbatim** and loaded **flat** (one managed Delta table each) into
the live Lakehouse the ontology binds to. So a DuckDB query over the CSVs is **byte-identical** to the bound
data — the oracle is independent of the model under test and reproducible by any third party with no Azure
access.

## Usage
```bash
python eval/ground_truth.py                 # regenerate ground_truth.json (offline)
python eval/run_baseline.py --dry-run-mock  # offline: validate harness+scorer, no live calls, no cost

# Live (requires: az login, .env with the Fabric IQ connection, and COST APPROVAL — Art. VIII):
python eval/scorer.py --model gpt-5.4
python eval/run_baseline.py --models gpt-5.4 gpt-5.4-mini --confirm-cost
```

## Cautions
- **Every dataset task issues real, billable model + Fabric IQ calls.** The matrix is cost-gated; confirm
  cost before running (Art. VIII / C9).
- The ontology **ON/OFF ablation was dropped**: with synthetic data an ungrounded agent trivially collapses
  to ~0% (tautological). Goal #2 is evidenced by the groundedness + multi-hop traversal metrics instead.
