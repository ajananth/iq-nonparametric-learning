# Recommended config — auditable text-diff vs Phase-5 baseline

The Phase-6 **recommended** agent config is the Phase-5 baseline with **one** frozen-weights TEXT edit:
a client-side row-injection change that drops 8 redundant `*_json` graph-serialization columns. Every
other surface — instructions, skill, tool/grounding descriptor, and the knowledge base itself — is
**byte-identical** to the Phase-5 baseline, so the grounding MECHANISM (retrieve + inject,
rerankerThreshold:0, dual-auth) and the retrieved evidence are unchanged (single-variable, Art. III).

```diff
# instructions.md                : UNCHANGED  (sha256 identical to baseline)
# skills/SKILL.md                : UNCHANGED  (sha256 identical to baseline)
# tools.json  grounding.descriptor: UNCHANGED  (sha256 identical to baseline)
# knowledge base (retrievalReasoningEffort / retrieval / answer instructions): UNCHANGED
#   reasoning=medium, no custom retrieval/answer instructions  -> NO re-provision required

# injection.json  (the ONLY change)
- baseline : {"include_synthesized_answer": true, "max_rows": null, "drop_columns": [], "max_row_chars": null}
+ optimized : {"include_synthesized_answer": true, "max_rows": null, "max_row_chars": null,
+              "drop_columns": ["Site_json","site_json","species_json","measurement_json",
+                               "treatment_record_json","hasTreatment_json",
+                               "hasMeasurement_edge_json","dominantSpecies_edge_json"]}
```

## Why this is accuracy-safe by construction

- The dropped columns are full JSON serializations of graph entities/edges that **duplicate** data already
  present as flat CSV columns (`site_name`, `scientific_name`, `measurement_count`, `chlorophyll_a_ugl`,
  `active_site_count`, `phylum`, …). The SQL ground truth is computed over the flat structured columns.
- Offline verification over all 24 held-out tasks confirmed **every** ground-truth value (10 scalars,
  8 sets) still appears in the trimmed payload — **0 tasks lose a scored cell**.
- The synthesized-answer block is **retained** (`include_synthesized_answer: true`) as a scalar safety net.
- For the 6 negative (unanswerable) tasks, dropping data can only make a safe refusal MORE likely — the
  refusal guardrail cannot regress by construction (empirically negatives held 6/6).

## Frozen-weights evidence

- `fine_tuning: false`, model is a deployment string, single config hash across the run
  (`f9a15da1c04b83904e3dd92b0802aec4072656b4a1b83bc4519587ff273da952`) — see
  `eval/scorecards/optimized_gpt-5.4.json` → `frozen_weights`. The deployment is unchanged; the only
  difference from baseline is text (this `injection.json`).
