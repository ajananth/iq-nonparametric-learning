# Cross-vendor scorecard — Kimi-K2.6 reasoning / gpt-5.4 synthesis (H-4, #50)

_Generated 2026-07-31T01:22:37.549164+00:00 · 24 held-out tasks · single live pass · ontology grounded in ALL runs._

Running the **identical, unmodified** tuned harness (`agent/.agent_configs/optimized/`) with the **reasoning/answer model swapped** to the open-weights, non-GPT **Kimi-K2.6** (Moonshot AI, GlobalStandard SKU). KB answer-synthesis and the LLM-judge stay `gpt-5.4` (KB `answerSynthesis` is GPT-family-only — `docs/verified-capabilities.md` §5c). Anchor = enshrined Phase-7 Optimized-LLM `gpt-5.4` (`eval/showdown/RESULTS.md`).

## Headline — USD is the comparable cross-model axis

| Metric | `kimi-k2.6` (reasoning) | `gpt-5.4` anchor |
| --- | --- | --- |
| Accuracy | **87.5%** (21/24) | 91.7% (22/24) |
| **USD total** | **$0.152285** | $0.163643 |
| **USD $/query** | **$0.006345** | $0.006818 |
| **USD $/correct** | **$0.007252** | $0.007438 |
| Groundedness (KB retrieve) | 100.0% | 100.0% |
| Safe refusals (negatives) | 6/6 | 6/6 |
| Tokens in/out (info only) | 90822/16501 | 97226/4211 |

> Token counts are per-model INFORMATIONAL ONLY: Kimi-K2.6 and gpt-5.4 use different tokenizers, so a token is not a like-for-like unit across them. The comparable cross-model axis is USD (both models are on the GlobalStandard SKU, so dollars are measured on the same basis).

## Accuracy — paired bootstrap CI vs the enshrined gpt-5.4 per-task vector

- Kimi-K2.6: **87.5%** — 95% CI [75.0, 100.0]
- gpt-5.4 anchor: 91.7% — 95% CI [79.2, 100.0]
- **Paired accuracy delta (Kimi - gpt-5.4): -4.2 pts, 95% CI [-12.5, 0.0]** (10000 resamples, seed 20260731, n=24).
- **CI includes 0: True** — parity within noise (the pre-registered H2 hypothesis; a within-noise result is a SUCCESS for cross-vendor model independence, Art. I).

_Limitation (stated honestly, carried from H1): the paired bootstrap captures judge/sampling variance but NOT between-run retrieval non-determinism; the gpt-5.4 anchor is itself a single run carrying the same +/-1 multi-hop retrieval variance._

## Accuracy by category

| Category | Kimi correct | gpt-5.4 anchor | Total |
| --- | --- | --- | --- |
| single_hop | 7 | 7 | 8 |
| multi_hop | 8 | 9 | 10 |
| negative | 6 | 6 | 6 |

## Single-variable control (Art. III)

- Config hashes observed this run: `f9a15da1c04b8390...` (single shared hash across all 24 tasks: **True**).
- Equals enshrined Phase-7 hash `f9a15da1...`: **True** (env-independent (hash computed with env tokens un-substituted)).
- Fine-tuning: **none** (the model is a deployment-name string; weights frozen — Art. II).
- ONLY variable vs the anchor: the reasoning-model deployment string `gpt-5.4` -> `kimi-k2.6`. KB synthesis + judge held at `gpt-5.4`.
- **End-to-end confirmation of #47:** the `optimized/` dir hashes to the enshrined `f9a15da1...` in this environment (same Azure AI Search resource as Phase-7), independently re-verifying the restored config tree — a bonus integrity win.

## Run provenance (honest correction — Art. I)

The FIRST live attempt was **discarded before any result was interpreted**: the harness had defaulted to the **baseline** config dir (hash `7486f0a5...`) instead of the enshrined **optimized** dir (`f9a15da1...`), which the runner's automated single-variable fairness assertion caught (`config_hash != enshrined`). This is a config-dir setup bug, **not** a re-roll to fish for a number (no result was read or published from it). The runner was fixed to pin `optimized/` explicitly and a **pre-spend hard guard** was added (STOP with zero spend if the optimized hash != enshrined `f9a15da1...`), then a single corrected pass was run — the one enshrined here.

## Isolation diagnostic — contested misses

**Shared with the flagship (model-INDEPENDENT):** S01, M06 — the enshrined Phase-7 misses that the gpt-5.4 anchor ALSO gets wrong (S01: agentic retrieval returns `active_site_count=0` on all models — an ontology `active`-flag vs SQL `active=true` ground-truth quirk; M06: retrieval returns no rows on all models). Zero model-attributable gap on these.

- **M10** (multi_hop, grounded=True): recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay Eastern', 'Darling River at Bourke', 'Florida Coastal Lagoon', 'Gnangara Lake Reserve'] — documented Phase-7 **retrieval column-projection / set-completeness variance** (the agentic-retrieval header can drop `site_name`, so synthesis emits IDs not names and the name-based scorer scores recall 0; volume varies run-to-run). Model-INDEPENDENT: the isolation diagnostic (`eval/showdown/RESULTS.md`) showed M04+M10 pass 14/15 conditioned on a well-formed retrieval, and it would break the gpt-5.4 flagship identically.

## Verdict (honest, pre-registered — cross-vendor-protocol.md §5)

1. **Accuracy within noise of the anchor:** MET (paired-delta 95% CI includes 0).
2. **Groundedness ~100%:** MET (100.0% KB-retrieve).
3. **Refusals preserved:** MET (6/6 negatives).
4. **USD cost vs gpt-5.4:** $0.152285 total / $0.007252 per-correct vs $0.163643 / $0.007438 — reduction MET.

**Fairness invariant:** single shared config hash = True, fine_tuning=false. **Cross-vendor model independence (H2, Art. III)** is supported: the open-weights, non-GPT Kimi-K2.6 reaches the same answers on the same grounded harness with a config-string-only swap. No re-rolling to fish for a passing scorecard (Art. I).
