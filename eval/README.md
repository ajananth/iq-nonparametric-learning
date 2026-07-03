# `eval/` — Agent Optimizer eval suite (Phase 6)

**Intent.** This directory holds the evaluation config and dataset that drive the **non-parametric
optimization** loop (Foundry Agent Optimizer, or the SkillOpt fallback). The files use the **verified
shapes** documented in `docs/verified-capabilities.md` §3c.

**Status: placeholders.** The real algal-bloom task dataset and criteria rubrics are authored in Phase 6.

## Files
- **`eval.yaml`** — verified optimizer config shape. Key facts (verified §3c):
  - `options.optimization_model` is **required** and must be one of **`gpt-5`, `gpt-5.1`, `gpt-5.3`**.
  - `options.eval_model` may be any deployed chat-completion model. **If it isn't deployed, all scores
    silently return 0.**
  - `options.optimization_config.model` (a list) enables the **model-selection** target (Phase 7).
- **`eval.jsonl`** — JSONL, one task per line, verified shape:
  `{"name", "prompt", "criteria": [{"name", "instruction"}], "groundTruth"?}`.

## Cautions (verified §3c)
- **Every dataset task invokes the agent**, executing any real tool calls — use synthetic fixtures / test
  endpoints to avoid charges and state mutation (Art. V).
- Score interpretation: `<0.03` noise · `0.03–0.10` moderate · `0.10–0.20` significant · `>0.20` major.
- Running `azd ai agent optimize` requires **allow-list** access (#10); otherwise use the **SkillOpt**
  fallback (`docs/verified-capabilities.md` §4).
