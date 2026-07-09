# `agent/` — Foundry agent harness (baseline, Phase 5)

> **Issue:** #24 (EPIC D, #4) · **Phase:** 5 (harness + eval + baseline)

**Intent.** The **non-parametric, text-space** configuration and invocation harness for the hosted Microsoft
Foundry agent, grounded in the **live** Fabric IQ `iqnpl_ontology` via the **Foundry IQ Knowledge Base**
(`fabricOntology`) **manual `/retrieve` + inject** path — the experiment surface that produced every committed
scorecard (`docs/verified-capabilities.md` §2b, Verified-by-test 2026-07-08). The native `fabric_iq_preview`
tool (§2a) is **not** the eval grounding path: its hosted-MCP tool-result chunker exposes **0 rows →
hallucination**, so it was **disqualified for the experiment on 2026-07-08** (§2a addendum); native KB attach
is the recommended **production** pattern (§2c). The model is a **swappable deployment-name string** — swapping
`gpt-5.4` ↔ `gpt-5.4-mini` is a config change with no code rewrite (Art. III); weights are never touched
(Art. II).

```
agent/
  agent.yaml               # hosted-agent manifest (model = ${FOUNDRY_MODEL_DEPLOYMENT_NAME}, swappable)
  harness.py               # load_config() + create/invoke/delete a Foundry agent version; captures metrics
  .agent_configs/
    baseline/
      instructions.md      # water-analyst persona  -> Instruction-tuning target
      tools.json           # fabric_iq_knowledge_base grounding (KB retrieve+inject) -> retrieval-descriptor optimization target (description only)
      skills/
        SKILL.md           # investigation skill body -> Skill-improvement target
```

## Grounding (verified-by-test, 2026-07-08)
`tools.json` declares a single **`fabric_iq_knowledge_base`** grounding block (not a native tool): an Azure AI
Search **agentic-retrieval Knowledge Base** over a **`fabricOntology`** knowledge source, consumed via the
manual **`/retrieve` + inject** path (`docs/verified-capabilities.md` §2b). At runtime `harness.py` POSTs the
question to `{AZURE_SEARCH_ENDPOINT}/knowledgebases/{kb}/retrieve` (dual-header OBO, so Fabric IQ resolves the
ontology over the bound OneLake data in the signed-in user's context), then **injects the returned verbatim
rows** into the agent context before it answers. `rerankerThreshold: 0` is load-bearing — without it the
default reranker filters multi-hop answers to empty (§2b). Infra refs (search endpoint / KB names) come from
`.env` via `AZURE_SEARCH_*` (never committed, Art. VI). **This is the path that produced every committed
scorecard.**

> **Why not the native `fabric_iq_preview` tool?** That tool (§2a) *is* the native/production-attach pattern,
> but Foundry's hosted-MCP tool-result chunker exposes **0 rows** from the ontology result → parametric
> hallucination, so it was **disqualified for this experiment on 2026-07-08** (§2a addendum). The native KB
> attach (`knowledge_base_retrieve`) grounds correctly and is the recommended **production** pattern, but it
> cannot pin `rerankerThreshold: 0` or return verbatim rows, so the eval uses the manual `/retrieve` + inject
> surface for its experimental controls (§2c).

## Non-parametric optimization (why this layout)
An agent is **optimizer-ready** when it loads these files via `load_config()`, so the *same code* runs with
or without the Agent Optimizer (Phase 6). The optimizer changes **only text/config** — instructions
(`instructions.md`), tool **descriptions** (`tools.json`), and skill **bodies** (`skills/`) — never weights
(Art. II) and never business logic (Art. III). Per **Art. IV** no table/column/SQL is baked into any of
these files; the agent reaches all semantics through the ontology knowledge base.

## Usage
```bash
pip install -r requirements.txt      # needs azure-ai-projects>=2.2.0
az login                             # delegated identity (no secrets stored)
cp .env.example .env                 # fill FOUNDRY_PROJECT_ENDPOINT, AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KNOWLEDGE_BASE, ...

# One-off smoke test (swap the model freely):
python agent/harness.py --model gpt-5.4      --prompt "How many monitored sites are active?"
python agent/harness.py --model gpt-5.4-mini --prompt "How many monitored sites are active?"
```

`harness.py` returns, per invocation: the answer, the Fabric IQ KB `/retrieve` call(s) — shaped as a
`fabric_kb_retrieve` tool-call record so the scorer's groundedness/traversal detection is unchanged —
input/output tokens, latency, and the config hash (fairness fingerprint). The evaluation
framework in `eval/` drives this harness across the question set.
