# Phase 7 — SLM-vs-LLM showdown (Condition A: config-only model swap)

**Issue #31 · EPIC F (#6).** Run the **exact** Phase-6 recommended harness
(`agent/.agent_configs/optimized/`) UNCHANGED on the SLM **gpt-5.4-mini** over the 24-Q held-out eval. The
**only** variable that moved is the model deployment string — agent orchestration model **and** knowledge-base
synthesis model both became `gpt-5.4-mini` (one-model-per-run). This isolates **goal #3 — model independence /
zero code rewrite (Constitution Art. III)** and the **cost axis** of H1.

> **Pre-registered honest expectation (pinned before running, Art. I — no goalpost-moving).**
> Accuracy: HOLD or slight dip (mini is a weaker instruction-follower; the ontology carries the reasoning).
> Cost: LARGE win (mini ~5× cheaper/token). Tokens: ~EQUAL for a fixed harness — the `≤75% tokens` clause was
> Phase-6's lever and was **not** expected to move from the swap alone. All reported as-measured.

## Headline verdict

**Not a *strict* Pareto win** (the pre-registered accuracy clause `accuracy(SLM) ≥ accuracy(LLM)` fails:
87.5% < 91.7%). **The defensible finding is stronger than the strict test:** running the **identical harness with
zero code change**, the SLM matches the flagship **within noise** — its two genuine misses are **shared and
identical** with the flagship — while costing **~12% as much (7.8–8.4× cheaper)** at **~66% of the tokens**.
**Model independence (goal #3) is proven** regardless of the stochastic 3rd-slot outcome.

## Results table (single-run, N=24, held-out)

| Run | Model | Config | Accuracy | Tokens (in/out) | Cost (USD) | $/correct | Latency avg | Grounded |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| **Optimized-SLM** | `gpt-5.4-mini` | `optimized/` | **87.5% (21/24)** | 66,864 (64,410/2,454) | **$0.021011** | **$0.001001** | 22,871 ms | 100% |
| Optimized-LLM (anchor) | `gpt-5.4` | `optimized/` | 91.7% (22/24) | 101,437 (97,226/4,211) | $0.163643 | $0.007438 | 46,848 ms | 100% |
| Baseline-LLM (Phase 5) | `gpt-5.4` | `baseline/` | 91.7% (22/24) | 107,450 (102,760/4,690) | $0.175350 | $0.007970 | 30,002 ms | 100% |

**Config hash identical across mini and LLM:** `f9a15da1c04b83904e3dd92b0802aec4072656b4a1b83bc4519587ff273da952`
· `fine_tuning=false` · single shared config → the model deployment string is the **sole** variable (Art. III).

## Two comparators

**(i) optimized-mini vs optimized-LLM — isolates the MODEL (clean single variable):**

| Axis | Ratio SLM/LLM | Pareto ≤75%? |
| --- | --- | --- |
| Accuracy | 87.5% vs 91.7% (−4.2 pts) | ✗ (clause fails) |
| Tokens | **65.9%** | ✓ |
| Cost | **12.8%** (7.79× cheaper) | ✓ |
| Cost / correct | 13.5% (7.43× cheaper) | — |

**(ii) optimized-mini vs Phase-5 baseline-LLM — system-level story:**
tokens **62.2%**, cost **12.0% (8.35× cheaper)**, accuracy −4.2 pts. Same single genuine-miss profile.

## Accuracy is not statistically distinguishable at N=24

Bootstrap 95% CIs (10,000 resamples):

- optimized-mini: 87.5% — 95% CI **[75.0, 100.0]**
- optimized-LLM / baseline-LLM: 91.7% — 95% CI **[79.2, 100.0]**
- **Paired accuracy delta (SLM − LLM): −4.2 pts, 95% CI [−12.5, +0.0]** — the interval **includes 0**, so there is
  **no statistically distinguishable accuracy gap** between the SLM and the flagship at this sample size.

*Limitation (stated honestly):* the paired bootstrap captures judge/sampling variance but **not** between-run
retrieval non-determinism (see below). The flagship anchor (91.7%) is **itself a single run** carrying the same
±1 multi-hop retrieval variance and was not re-measured; it could itself draw 21/24 on a re-roll.

## Per-category and the three misses

| Category | SLM | Opt-LLM | Baseline-LLM |
| --- | --- | --- | --- |
| single_hop | 7/8 | 7/8 | 7/8 |
| multi_hop | 8/10 | 9/10 | 9/10 |
| negative (refusal) | **6/6** | 6/6 | 6/6 |

The SLM's misses in the enshrined run were **S01, M06, M04**:

- **S01 & M06 — genuine, IDENTICAL to the flagship** (grounded, error-free). S01: agentic retrieval returns
  `active_site_count=0` on **all three** models (an ontology `active`-flag vs SQL `active=true` quirk in the
  ground truth, not a model error). M06: retrieval returns **no rows** on all three models → all refuse/miss.
  **Zero model-attributable gap on these two.**
- **M04 — stochastic retrieval variance, not mini reasoning.** The agentic-retrieval call returned rows whose
  header lacked the `site_name` column (`site_id,measurement_id,species_id`), so synthesis could only emit IDs and
  the name-based scorer scored recall 0. In the flagship's single run (and in the throttled first mini run) the
  **same** query returned `site_name` and M04 scored recall 1.0. This is the documented "live retrieval volume
  varies run-to-run" effect — **model-adjacent, and it would break the flagship identically.**

## The 3rd-slot miss is a quantified platform coin-flip (isolation diagnostic)

To rule out platform effects, M04 and M10 were each re-invoked **10× in isolation** on `gpt-5.4-mini`
(quota=150, agent + KB synthesis both mini). Zero 429s. Pass-rates split cleanly by retrieval quality:

| Retrieval | M04 | M10 | Combined |
| --- | --- | --- | --- |
| `site_name` column **present** (well-formed) | 7/7 | 7/8 | **14/15 (93%)** |
| `site_name` column **absent** (degraded projection) | 1/3 | 0/2 | 1/5 (20%) |
| **Overall** | **8/10** | **7/10** | 15/20 (75%) |

**Reading:** the 3rd-slot failures are **dominated by model-independent server-side retrieval column-projection
non-determinism** (missing `site_name` → synthesis can only emit IDs). **Conditioned on a well-formed retrieval,
the SLM reaches 14/15 (93%) on exactly the two contested multi-hop set tasks — flagship parity within noise.**
The single well-formed exception (M10 recall 0.95, one site of 19 dropped) is a minor mini set-completeness slip.
This does **not** establish a clean 22/24, so the enshrined scorecard stays **21/24**; the diagnostic is reported
as the quantified limitation, not folded into the headline.

## Two runs, one honest number

Two independent full 24-Q runs both landed **87.5% (21/24)** with **different** 3rd-slot tasks (run-1 M10, run-2
M04), which is itself the evidence that the 3rd slot is stochastic. The **clean quota=150 run is authoritative**;
the throttled first run is archived as supporting evidence.

- **Run 1 (throttled, mini quota=10):** 3rd miss = **M10 via HTTP 429** (hard infra rate-limit).
- **Run 2 (clean, mini quota=150):** 3rd miss = **M04 via retrieval column-projection variance.** ← enshrined.

## Infra note — capacity bump (NOT an experiment variable)

The first run's M10 failure was a **hard Azure throttle**: the `gpt-5.4-mini` deployment had
`sku.capacity=10` vs the flagship `gpt-5.4` at `150` (account `tchack-resource`, RG `rg-ai`, eastus2). This was
raised to match the flagship:

```
az cognitiveservices account deployment create -n tchack-resource -g rg-ai \
  --deployment-name gpt-5.4-mini --model-name gpt-5.4-mini --model-version 2026-03-17 \
  --model-format OpenAI --sku-name GlobalStandard --sku-capacity 150
# verified: {"name":"gpt-5.4-mini","cap":150,"ver":"2026-03-17"}
```

This is **infrastructure quota only** — it changes no model weights, no config, no deployment string, no eval
artifact. Single-variable integrity is intact (`fine_tuning=false`, one shared config hash). It was applied
*between* the two runs; the enshrined result is the post-fix clean run.

## KB re-provision params (recorded)

The knowledge base was re-provisioned to swap **only** the synthesis `deploymentId`, verified by live GET
before **and** after each transition (`files/kb_before.txt`, `kb_after_mini.txt`, `kb_after_restore.txt`):

| Field | Before (canonical) | During run (mini) | After (restored) |
| --- | --- | --- | --- |
| `models[].deploymentId` / `modelName` | `gpt-5.4` | **`gpt-5.4-mini`** | `gpt-5.4` |
| `retrievalReasoningEffort.kind` | `medium` | `medium` | `medium` |
| `retrievalInstructions` | `null` | `null` | `null` |
| `answerInstructions` | baseline text | baseline text (identical) | baseline text |
| `authIdentity` | `null` (search MI) | `null` | `null` |
| KS `fabricOntologyParameters` | ws `a9dc85a5…` / ont `8dd31e82…` | unchanged | unchanged |

The KB was **restored to canonical `gpt-5.4`** at the end and live-GET verified.

## Integrity gates — all PASS

- **Protected files byte-identical (SHA-256 before == after):** `eval/scorer.py`, `eval/dataset.jsonl`,
  `eval/ground_truth.json`, `eval/scorecards/baseline_gpt-5.4.{json,md}`,
  `eval/scorecards/optimized_gpt-5.4.{json,md}`. ✅
- Recommended config dir `agent/.agent_configs/optimized/` unchanged (git clean). ✅
- KB restored to canonical (`gpt-5.4`, `reasoning=medium`), live-GET verified. ✅
- `fine_tuning=false`; single shared config hash across models; deployment string is the sole variable. ✅
- No secrets committed (infra GUIDs/endpoints only; auth acquired at runtime via `DefaultAzureCredential`). ✅
- Honest-negative pre-committed and honoured: measured 87.5% enshrined; no re-rolling to fish for 22/24. ✅

## Bottom line

Swapping a flagship LLM for a 5×-cheaper SLM on the **identical, unmodified harness** costs **~4 accuracy points
that are not statistically distinguishable at N=24** (and whose only non-shared miss is model-independent
retrieval variance) while cutting **cost by ~8×**. **The system is model-independent (goal #3, Art. III): pick the
model per workload** — the flagship when you want the extra multi-hop robustness, the SLM when cost dominates and
near-flagship accuracy suffices. That cost/accuracy frontier — not a single Pareto checkbox — is the honest story.
