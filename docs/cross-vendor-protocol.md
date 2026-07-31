# Cross-vendor protocol — H2 (open-weights, non-GPT model under the same Fabric IQ harness)

> **Issue:** #48 (EPIC H, #46) · **Phase:** H (cross-vendor extension) · **Status:** PRE-REGISTERED
> (authored **before** the cross-vendor eval, #50) · **Author:** H-2 child session · **Date:** 2026-07-31
> **Governs / governed by:** Constitution Art. I (accuracy, no goalpost-moving), Art. II (frozen weights),
> Art. III (model independence), Art. V (cost transparency), Art. VIII (human-in-the-loop + cost), Art. XIII
> (Epic→Issue→PR).
> **Source of truth for capability claims:** `docs/verified-capabilities.md` (primary Microsoft/Azure
> sources only). This protocol adds no new capability claims of its own; where it references platform
> behaviour it points back to that note.

This document **pre-registers** the hypothesis, experimental setup, single-variable control, metrics, and
success criteria for the **cross-vendor** experiment **before** any live eval is run (#50). Pre-registration
guards against post-hoc metric-shopping: the criteria below are fixed now — dated and authored ahead of the
run — and the eval reports against them, **including if the result is negative** (Art. I).

Where the published H1 result (`docs/experiment-protocol.md`) proved model independence **within one vendor**
(flagship `gpt-5.4` ↔ small `gpt-5.4-mini`, both OpenAI, on the identical tuned harness), H2 asks the harder
question: does that independence hold **across vendors**, when the reasoning/answer model is an
**open-weights, non-GPT** model from a different provider?

---

## 1. Hypothesis

**H2.** Running the **identical, unmodified** tuned harness (`agent/.agent_configs/optimized/` — the Phase-6
recommended config) with the **reasoning/answer model swapped** to the open-weights, non-GPT **Kimi-K2.6**
(Moonshot AI; deployed **Direct-from-Azure** on the **GlobalStandard** SKU) will:

- **(a) Hold accuracy at flagship parity WITHIN NOISE** on the 24-question held-out set (`eval/dataset.jsonl`),
  measured against the enshrined `gpt-5.4` anchor (91.7%, 22/24 — `eval/showdown/RESULTS.md`);
- **(b) Keep groundedness ~100%** — the harness enforces the Fabric IQ **KB retrieve** step
  (`fabric_kb_retrieve`) on every task, so grounding does not depend on the model's parametric knowledge;
- **(c) Preserve correct refusals** — the six negative / out-of-domain questions still fail safe (decline
  without fabricating);
- **(d) Deliver a COST REDUCTION vs the frontier `gpt-5.4`**, measured in **USD**.

**Rationale (the project thesis, extended).** H1 established that when enterprise context and
reasoning-over-joins live in the **Fabric IQ ontology** rather than in the model's weights, a cheaper model
suffices for the same answers — the "non-parametric learning" claim (Art. II/III). H2 extends the claim past
the vendor boundary: if the ontology's **NL2Ontology** layer truly offloads schema reasoning, joins, and
multi-hop traversal to **Fabric's engine**, then even an **open-weights model from a different vendor** —
sharing no lineage, tokenizer, or training pipeline with GPT — should reach the same answers on the same
harness with **zero code change** (a config-string model swap, Art. III).

**Honest expectation (Art. I, no goalpost-moving).** Points (a)–(d) above are stated **as the expectation**,
not as a foregone conclusion. The success criteria in §5 are fixed here, before the run. A result where
Kimi-K2.6 **misses** parity within noise, or **fails** to reduce USD cost, is a valid, reportable outcome —
it would bound the model-independence claim rather than break the protocol.

**Null (H0).** The cross-vendor swap cannot reach flagship-parity accuracy within the stated noise band on
the identical harness, i.e. the model-independence result does **not** generalise across vendors.

---

## 2. Experimental setup

State factually — this is the tested **configuration**, not a limitation.

| Role | Model | How set |
| --- | --- | --- |
| **Reasoning / answer model** (the variable) | **Kimi-K2.6** (Moonshot AI), open-weights, non-GPT | config only — env / `--model` deployment string |
| KB answer-synthesis (retrieval-side) | `gpt-5.4` | platform-managed component of the `fabricOntology` knowledge base |
| LLM-as-judge (scoring) | `gpt-5.4` | held byte-identical to Phase 5–7 |

**What "cross-vendor" means here.** The model performing the **cross-domain reasoning** and **producing the
answer** is the open-weights **Kimi-K2.6** — that is the essence of the cross-vendor claim. It reads the
grounded rows, resolves the multi-hop question, and writes the final answer.

**On the KB answer-synthesis step.** The Fabric IQ **Foundry IQ Knowledge Base** (`fabricOntology`) includes
a lightweight, platform-managed **answer-synthesis** component on the retrieval side, which — per the
platform's requirements (`docs/verified-capabilities.md` §2b: a `fabricOntology` KB **must** specify an Azure
OpenAI synthesis model; there is no extractive/`minimal` mode) — runs on `gpt-5.4`. This is a fixed property
of the retrieval path, held **byte-identical** across every model in this study (and across Phase 5–7). It is
part of the grounding mechanism, not the reasoning agent. We document it here for completeness; it is
**not** a constraint or limitation on the cross-vendor claim, because the model doing the reasoning and
emitting the answer is Kimi-K2.6.

**Frozen weights (Art. II).** No fine-tuning occurs anywhere. The reasoning model is referenced by
**deployment name**; swapping GPT → Kimi-K2.6 is a config-string change with **no code rewrite** (Art. III).
The scorecard records `frozen_weights.fine_tuning = false` on every run.

### Single-variable control (the core of the experiment)

Across **every** run in this study, the following are **byte-for-byte identical** to the enshrined Phase 5–7
runs; the **only** thing that changes is the reasoning/answer model deployment string:

- the tuned harness — `agent/.agent_configs/optimized/` (`instructions.md`, `tools.json`, `skills/`,
  `injection.json`, `kb_params.json`), the Phase-6 recommended config,
- the ontology (`iqnpl_ontology`) and its bound OneLake data,
- the KB grounding mechanism (KB retrieve + inject, `rerankerThreshold: 0`, dual-auth) **and** its
  `gpt-5.4` answer-synthesis model,
- the eval question set (`eval/dataset.jsonl`, 24 Q),
- the SQL ground-truth oracle (`eval/ground_truth.py` / `eval/ground_truth.json`),
- the scorer (`eval/scorer.py`), the judge model (`gpt-5.4`), and the pricing table
  (`eval/pricing.json` — an operator-supplied rate, **flagged not a verified Microsoft price**, Art. I).

The harness records a **config hash** on every task. The reasoning-model deployment string is **excluded**
from the hash (it is the variable under test), so a correct cross-vendor swap yields the **same enshrined
Phase-7 config hash** — the auditable proof that only the model moved. That hash is
**`f9a15da1c04b83904e3dd92b0802aec4072656b4a1b83bc4519587ff273da952`** (short `f9a15da1…`).

> **Note (hash reconciliation, #47).** Issue #47 is reconciling the enshrined Phase-7 config-hash value
> across artifacts. This protocol references **the enshrined Phase-7 config hash**; if #47 has merged by the
> time the eval (#50) runs, cite the reconciled value from that issue in the scorecard.

---

## 3. Metrics

All emitted per-task and aggregated by `eval/scorer.py` into `eval/scorecards/`, on the **same instrument**
used for Phase 5–7 (single-variable — see §2).

### 3.1 Accuracy (hybrid oracle)
Unchanged from `docs/experiment-protocol.md` §3.1. **SQL-primary** (deterministic answer over the four source
tables, 1% numeric tolerance, full-recall on sets; the named oracle is authoritative, Art. I) plus
**LLM-as-judge** second opinion (`gpt-5.4`) — the judge is primary for the negative/refusal questions
(safely declined without fabricating). Both `sql_correct` and `judge_correct` are recorded.

### 3.2 Cost — the headline cross-model axis (IMPORTANT)

> **The comparable headline cost axis is USD: `$/query` and `$/correct`.**

USD is directly comparable across models because **all** models in this study — `gpt-5.4`, `gpt-5.4-mini`,
and **Kimi-K2.6** — are deployed on the **same GlobalStandard SKU**, so the dollars are measured on the same
basis. There is **no deployment-basis caveat**. `$/query` and `$/correct` are computed from
`eval/pricing.json` (Art. I: operator-supplied rate, not a verified Microsoft price) and are the numbers the
H2 cost claim (§1d, §5) is judged on.

**Raw token counts are reported per-model for information ONLY.** GPT and Kimi use **different tokenizers**,
so a token is not a like-for-like unit between them. Token **counts** must **never** be used to support a
cross-model *"used fewer tokens"* claim. Any cross-model efficiency statement is made in **USD only**.
(Within a single tokenizer family, e.g. GPT↔GPT, token counts remain informative — that is a Phase-6/7
concern, not an H2 cross-vendor one.)

### 3.3 Groundedness & traversal-correctness
Unchanged from §3.5 of `docs/experiment-protocol.md`. From the tool-call logs: did the agent call the Fabric
IQ **KB retrieve** (`fabric_kb_retrieve`)? For multi-hop questions, **traversal-correctness** is credited when
the tool was called **and** the answer matches ground truth. Because grounding is **harness-enforced**,
groundedness is expected at ~100% independent of the reasoning model.

### 3.4 Refusal safety
Negative-case safe-refusal rate (no fabrication) on the six out-of-domain questions — a guardrail carried
over identically from Phase 5–7.

### 3.5 Frozen-weights evidence
Per run: the reasoning-model deployment string, the config hash (expected = enshrined Phase-7 hash),
`fine_tuning=false`, and `single_config` across the matrix — the auditable proof of Art. II/III compliance
across the vendor boundary.

---

## 4. Eval-set composition

**Byte-identical** to `docs/experiment-protocol.md` §4 — the same held-out 24-question set is reused so the
cross-vendor scorecard is scored on the same instrument as the published H1 result.

`eval/dataset.jsonl` — 24 questions over the algal-bloom domain:

| Category | Count | Purpose |
| --- | --- | --- |
| `single_hop` | 8 | Filters/aggregates on one entity — sanity + floor accuracy. |
| `multi_hop` | 10 | Cross-relationship traversal — the ontology's differentiating value. |
| `negative` | 6 | Unanswerable / out-of-domain — must fail safe, **not hallucinate**. |

Each answerable question carries a committed SQL query and a regenerated expected answer; negatives carry an
`answer_type: refusal`. The set is fixed; **no** questions are added, removed, or mutated for the
cross-vendor run.

---

## 5. Success criteria (pre-registered)

Fixed here, before the eval (#50). A negative result on any clause is a valid, reportable outcome (Art. I).

**Primary — cross-vendor model independence (H2):**

> The cross-vendor swap **holds** iff **all** of the following are met on the 24-Q held-out set, with only
> the reasoning-model string changed and the config hash equal to the enshrined Phase-7 hash:
>
> 1. **Accuracy within noise of the anchor** — `accuracy(Kimi-K2.6)` is within a **stated noise band** of the
>    `gpt-5.4` anchor (91.7%, 22/24). The band is the paired-delta 95% CI methodology already used for H1
>    (`docs/experiment-protocol.md` §5): the accuracy gap is "within noise" iff its **95% CI includes 0**.
> 2. **Groundedness ~100%** — the harness-enforced KB retrieve fires on every answerable task.
> 3. **Refusals preserved** — negative-case safe-refusal held at the Phase-5–7 level (no fabrication).
> 4. **USD cost reduction** — a **measured `$/query` and `$/correct` reduction vs `gpt-5.4`** (same
>    GlobalStandard SKU basis; §3.2).

**Interpretation.** Clauses 1–3 test whether the open-weights, non-GPT model reaches the **same answers** on
the **same grounded harness**; clause 4 tests the **economic** payoff. Reporting is honest either way: if
accuracy falls outside the noise band, or no USD cost reduction is measured, the protocol reports the failure
and the model-independence claim is **bounded to within-vendor** until further evidence. As in H1, we do not
re-roll runs to fish for a passing scorecard.

**Fairness invariant (must hold regardless of outcome):** a **single shared config hash** (the enshrined
Phase-7 hash) across models, and `fine_tuning=false` everywhere — the auditable Art. II/III proof.

---

## 6. Cost STOP-gate (Art. VIII)

The live cross-vendor eval (#50) is **cost-gated** and requires **explicit human approval before any live
Kimi-K2.6 call**. No live/tenant/cost operation is authorised by this pre-registration document. The offline
portions (ground-truth regeneration) run with **no** live calls and **no** cost; only the live scoring step
incurs spend, and it is blocked behind the human cost-confirmation flag below.

---

## 7. Reproducibility

Consistent with `docs/experiment-protocol.md` §6.

```bash
# 1. Regenerate the deterministic ground truth (offline; no Azure, no cost).
python eval/ground_truth.py

# 2. Score the cross-vendor model (LIVE; requires the Fabric IQ connection + prior human cost approval, §6).
#    scorer.py has no cost flag — the §6 STOP-gate is procedural / enforced at the run_baseline level.
python eval/scorer.py --model kimi-k2.6

# 3. Cross-vendor comparison vs the gpt-5.4 anchor (LIVE; cost-gated).
python eval/run_baseline.py --models gpt-5.4 kimi-k2.6 --confirm-cost

# Offline validation of the harness/scorer with no live calls or cost:
python eval/run_baseline.py --dry-run-mock
```

Outputs land in `eval/scorecards/`. The cross-vendor scorecard records the reasoning-model deployment string,
the config hash (expected = enshrined Phase-7 hash), `fine_tuning=false`, USD `$/query` and `$/correct`, and
the per-model informational token counts (§3.2).
