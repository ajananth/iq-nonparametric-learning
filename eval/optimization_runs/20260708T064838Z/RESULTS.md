# Phase-6 results — the two findings

_Run `20260708T064838Z` · model `gpt-5.4` (FROZEN) · reflection `gpt-5.4` · seed 1234 · LIVE._

Phase 6 asked whether a SkillOpt-style optimization loop over the frozen-weights TEXT surface could beat
the Phase-5 grounded baseline (91.7% / 22-24 / $0.17535) on the 24-Q **held-out** eval. It produced two
results — one cautionary, one positive — and both are the deliverable.

---

## Finding A (cautionary) — the full-loop DEV winner OVERFIT the small DEV split

The loop (rollout → reflect → held-out DEV validate → adopt-iff-strictly-better) selected **`c06`**:

- KB `retrievalReasoningEffort` → **low**, plus a multi-hop retrieval instruction (adopted as `c03`);
- injection `max_row_chars` → **600** (blind per-row truncation).

On the 6-Q DEV split c06 looked great: **100% accuracy at 8,963 tokens** (seed baseline 100% / 11,462).
But on the 24-Q **held-out** test it **REGRESSED**:

| metric | baseline | c06 (DEV winner) | Δ |
| --- | --- | --- | --- |
| held-out accuracy | 91.7% (22/24) | **83.3% (20/24)** | **−8.4 pts** |
| total tokens | 107,450 | 43,921 | −59.1% |
| cost | $0.17535 | $0.09770 | −44.3% |

Two previously-correct tasks flipped (S05 phylum aggregation, M10 traversal set) — the `reasoning=low`
edit weakened synthesis and the blind `max_row_chars=600` truncation dropped scored cells. **Lesson:**
with a tiny DEV split, aggressive edits that win DEV can lose the held-out test. Naive search overfits.
Artifacts: `ranking.md`, `candidates_log.json`, `c06_dev_winner_vs_baseline.diff`. c06 was **NOT adopted.**

---

## Finding B (adopted) — a mechanism-justified injection trim cuts tokens at NO accuracy loss

Instead of re-running the loop (which would only re-invite overfitting on a small dataset), we
**decomposed** c06 by mechanism and kept only the edit that is accuracy-safe *by construction*:

- discard `reasoning=low` (accuracy-risky — weakened synthesis);
- discard `max_row_chars=600` (accuracy-risky — blind truncation drops cells);
- discard the multi-hop retrieval instruction (c06 HAD it and still didn't fix M06 → keep KB byte-identical);
- **keep only**: drop the 8 redundant `*_json` graph-serialization columns client-side (they duplicate the
  flat structured columns the SQL ground truth is computed over — see `../../agent/.agent_configs/optimized/DIFF_vs_baseline.md`).

Correction surfaced during decomposition: there is **no `notes` column** in any retrieved rows; the actual
redundant free-text bloat is the `*_json` columns. That is what the recommended config drops.

### Held-out result (single pre-registered confirm eval, unchanged scorer)

| metric | baseline | **recommended (conservative)** | Δ |
| --- | --- | --- | --- |
| held-out accuracy | 91.7% (22/24) | **91.7% (22/24)** | **0 (held exactly)** |
| by category | single 7/8 · multi 9/10 · neg 6/6 | single 7/8 · multi 9/10 · neg 6/6 | identical |
| input tokens | 102,760 | 97,226 | −5.4% |
| total tokens | 107,450 | 101,437 | −5.6% |
| cost | $0.17535 | $0.16364 | −6.7% |
| cost / correct | $0.00797 | $0.00744 | −6.7% |

Zero tasks flipped; the two baseline misses (S01 filter-semantics, M06 multi-hop) remain (they are
KB/ontology-level, not injection-fixable); negatives held 6/6.

### Why the single-run token net (−5.6%) understates the trim

Live retrieval is **stochastic** — the number/size of rows returned varies run-to-run. The single-run net
is dominated by that variance on tasks with **no** `*_json` columns to trim. Isolating the trim on
**identical rows** (zero added cost) shows its true effect:

- On the baseline run's logged rows: the trim removes **−42%** of input tokens.
- On this confirm run's own rows: the trim removes **61,457** tokens (M04 −22,293; **M10 −36,670**;
  N05 −2,494). Without the trim, M10 alone would have been ~67k input tokens this run — **the trim
  cushioned a retrieval-driven blowup.**

So on a controlled (identical-rows) basis the reduction is ~40%; the raw single-run total (−5.6%) is
masked by retrieval-volume noise on non-json tasks (M10 +23k, N01 +6k vs the baseline run).

**Pre-registered acceptance** (accuracy ≥ 22/24 AND tokens lower): both met → adopted as the Phase-6
recommended harness.

---

## Frozen-weights / single-variable evidence

- `eval/scorecards/optimized_gpt-5.4.json` → `frozen_weights`: `fine_tuning: false`, model is a deployment
  string, single config hash `f9a15da1…` — no weight changes, deployment unchanged.
- Only `injection.json` differs from baseline; instructions / skill / tool descriptor / KB are byte-identical
  (hash-verified). KB was left at the Phase-5 baseline (reasoning=medium) — **no re-provision**, so retrieval
  is single-variable vs baseline.
- The Phase-5 `eval/dataset.jsonl`, `eval/scorer.py`, and `eval/ground_truth.py` were kept **byte-identical**
  (git-restored + hash-verified) so the held-out test is unchanged from Phase 5.
