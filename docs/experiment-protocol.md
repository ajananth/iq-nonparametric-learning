# Experiment protocol — H1 (SLM vs LLM under Fabric IQ grounding)

> **Issue:** #24 (EPIC D, #4) · **Phase:** 5 · **Status:** PRE-REGISTERED (authored before Phase 6
> optimization) · **Author:** Phase 5 child session · **Date:** 2026-07-06
> **Governs / governed by:** Constitution Art. I (accuracy), Art. II (frozen weights), Art. III (model
> independence), Art. IV (semantics in the ontology), Art. VIII (human-in-the-loop + cost), Art. XIII
> (Epic→Issue→PR).

This document **pre-registers** the hypothesis, comparison matrix, metrics, and success criteria for the
non-parametric SLM-vs-LLM experiment **before** any optimization is applied (Phase 6). Pre-registration
guards against post-hoc metric-shopping: the criteria below are fixed now; Phase 6/7 report against them.

---

## 1. Hypothesis

**H1.** An optimized, Fabric-IQ-grounded **small language model** (`gpt-5.4-mini`) can **match or beat** the
**large language model** (`gpt-5.4`) on task accuracy while using **far fewer tokens and far less cost** —
because the ontology's **NL2Ontology** layer offloads schema reasoning, joins, and multi-hop traversal to
**Fabric's engine**, not the model's parametric weights.

**Rationale (the project thesis).** If enterprise context and reasoning-over-joins live in the Fabric IQ
ontology rather than in the model, then a smaller, cheaper model should suffice for the same answers. This
is the "non-parametric learning" claim: optimize the harness/prompts/tools/model-selection in **text space**
(Art. II), never the weights.

**Null (H0).** The SLM cannot reach the LLM's accuracy without a disproportionate loss, i.e. there is no
Pareto-improving SLM configuration.

---

## 2. Comparison matrix

Baseline (Phase 5) and optimized (Phase 6) runs share **one** eval set and **one** ground-truth oracle.

| Run | Model deployment | Ontology grounding | Config | Phase |
| --- | --- | --- | --- | --- |
| Baseline-LLM | `gpt-5.4` | **ON** (all runs) | `agent/.agent_configs/baseline/` | 5 |
| Baseline-SLM | `gpt-5.4-mini` | **ON** (all runs) | `agent/.agent_configs/baseline/` (identical) | 5 |
| Optimized-LLM | `gpt-5.4` | **ON** | optimizer output | 6 |
| Optimized-SLM | `gpt-5.4-mini` | **ON** | optimizer output | 6 |

**Dropped: the ontology ON/OFF ablation.** With synthetic data, an ungrounded agent has no way to know the
values and collapses to ~0% — a tautological result. Goal #2 ("Fabric IQ drives the answers") is instead
evidenced by the **groundedness** and **multi-hop traversal-correctness** metrics (§3.5) plus multi-hop
success rate: the agent demonstrably calls `fabric_iq_preview` and the ontology resolves the joins.

### Single-variable fairness control (the core of the experiment)

Across **every** run, the following are **byte-for-byte identical**; the **only** thing that changes is the
model deployment string:

- the ontology (`iqnpl_ontology`) and its bound OneLake data,
- the agent config (`instructions.md`, `tools.json`, `skills/`) — enforced by a **config hash** recorded on
  every task; the comparison asserts a single shared hash across models (Art. III),
- the eval question set (`eval/dataset.jsonl`),
- the SQL ground-truth oracle (`eval/ground_truth.json`),
- the scorer, judge model, and pricing table.

**Frozen weights (Art. II).** No fine-tuning occurs anywhere. The model is referenced by **deployment name**;
swapping LLM↔SLM is a config-string change with **no code rewrite** (Art. III). The scorecard records
`frozen_weights.fine_tuning = false` on every run.

---

## 3. Metrics (six families)

All emitted per-task and aggregated by `eval/scorer.py` into `eval/scorecards/`.

### 3.1 Accuracy (hybrid oracle)
- **SQL-primary:** each answer is checked against a deterministic answer computed by SQL over the four
  source tables (`eval/ground_truth.py`, DuckDB over `data/*.csv`, which are byte-identical to the bound
  managed Delta tables). Scalars use a 1% numeric tolerance; sets require **full recall** of expected
  members; the named-oracle is authoritative (Art. I).
- **LLM-as-judge (second opinion):** a judge model (`gpt-5.4`) grades semantic consistency and, for the
  negative/guardrail questions, whether the agent **safely declined without fabricating**. Both signals are
  recorded (`sql_correct`, `judge_correct`); the SQL oracle is primary for answerable questions and the
  judge is primary for refusals.

### 3.2 Tokens
Input and output tokens per task (Responses API `usage`), plus totals and per-task averages.

### 3.3 Cost
`$/task` from `eval/pricing.json` (operator-supplied rates, **flagged not a verified Microsoft price** —
Art. I) and the aggregate **cost-per-correct-answer**. The H1 conclusion depends on the **cost/token RATIO**
between models, which is robust to the absolute rate.

### 3.4 Latency
Wall-clock ms per task; aggregate avg / p50 / p95 / max.

### 3.5 Groundedness & traversal-correctness
From the tool-call logs: did the agent call `fabric_iq_preview` (groundedness)? For multi-hop questions,
**traversal-correctness** is credited when the tool was called **and** the answer matches ground truth —
evidence the ontology resolved the multi-relationship path (e.g.
`Site→hasMeasurement→WaterQualityMeasurement→dominantSpecies→AlgaeSpecies`). Raw dispatched queries are
retained per task for audit.

### 3.6 Frozen-weights evidence
Per run: the model deployment string, the config hash, `fine_tuning=false`, and `single_config` across the
matrix. This is the auditable proof of Art. II/III compliance.

---

## 4. Eval set composition

`eval/dataset.jsonl` — 24 questions over the algal-bloom domain:

| Category | Count | Purpose |
| --- | --- | --- |
| `single_hop` | 8 | Filters/aggregates on one entity — sanity + floor accuracy. |
| `multi_hop` | 10 | Cross-relationship traversal — the ontology's differentiating value. |
| `negative` | 6 | Unanswerable / out-of-domain — must fail safe, **not hallucinate**. |

Each answerable question carries a committed SQL query and a regenerated expected answer; negatives carry an
`answer_type: refusal`. The set is fixed for the whole experiment.

---

## 5. Success criteria (pre-registered)

**Primary — H1 Pareto win (evaluated in Phase 6, criterion fixed here):**

> The SLM configuration is a **Pareto win** iff **accuracy(SLM) ≥ accuracy(LLM)** **AND** the SLM uses
> **≤ 75% of the LLM's total tokens** **AND** **≤ 75% of the LLM's total cost**.

`eval/run_baseline.py` computes this automatically (`h1_pareto.pareto_win`).

**Secondary / supporting:**
- Groundedness ≥ 95% (the agent actually uses Fabric IQ), on both models.
- Multi-hop traversal-correctness materially > 0 on both models (the ontology resolves joins).
- Negative-case safe-refusal ≥ 90% (no fabrication) — a guardrail, tracked but not part of the Pareto test.
- Fairness invariant holds: **single shared config hash** across models; `fine_tuning=false` everywhere.

**Interpretation of the Phase-5 baseline.** The baseline scorecard is the **starting point**, not the H1
verdict. H1 is judged after Phase 6 optimization. If the baseline already shows a Pareto win, that is
reported as a strengthening result; if not, Phase 6's non-parametric optimization is what the hypothesis
expects to close the gap.

---

## 6. Reproducibility

```bash
# 1. Regenerate the deterministic ground truth (offline; no Azure).
python eval/ground_truth.py

# 2. Score one model (live; requires the Fabric IQ connection + cost approval).
python eval/scorer.py --model gpt-5.4

# 3. Full baseline matrix + H1 comparison (live; cost-gated).
python eval/run_baseline.py --models gpt-5.4 gpt-5.4-mini --confirm-cost

# Offline validation of the harness/scorer with no live calls or cost:
python eval/run_baseline.py --dry-run-mock
```

Outputs land in `eval/scorecards/` (`baseline_<model>.{json,md}` and `baseline_comparison.{json,md}`).
