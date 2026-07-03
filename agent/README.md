# `agent/` — Foundry agent harness (baseline config)

**Intent.** This directory holds the **non-parametric, text-space** configuration of the hosted Foundry
agent. Following the verified `azd ai agent init` layout, the optimizer-tunable artifacts live under
`.agent_configs/baseline/` (see `docs/verified-capabilities.md` §3a–3b):

```
agent/
  .agent_configs/
    baseline/
      instructions.md     # system prompt  → Instruction-tuning target
      tools.json          # tool descriptions → Tool-optimization target
      skills/
        SKILL.md          # skill body      → Skill-improvement target
```

**Status: placeholders.** These are minimal, model-agnostic stubs. Real personas, tool wiring, and skills
land in Phase 5 (harness) and are optimized in Phase 6.

## Non-parametric optimization (why this layout)
An agent is **"optimizer-ready"** when it loads these files via `load_config()`, so the *same code* runs with
or without the optimizer. The optimizer changes **only text/config** — never model weights (Art. II) and
never business logic (Art. III). Optimization targets auto-activate from what's present here:
- `instructions.md` present → **instruction tuning**
- `tools.json` present → **tool optimization** (descriptions only; never types/defaults/required)
- `skills/*/SKILL.md` present → **skill improvement** (skill bodies)

Per **Art. IV**, no raw SQL or schema is coupled into these files — the agent reaches the semantics through
the `fabric_iq_preview` tool over the ontology.
