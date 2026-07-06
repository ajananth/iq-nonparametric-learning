# `agent/` — Foundry agent harness (baseline, Phase 5)

> **Issue:** #24 (EPIC D, #4) · **Phase:** 5 (harness + eval + baseline)

**Intent.** The **non-parametric, text-space** configuration and invocation harness for the hosted Microsoft
Foundry agent, grounded in the **live** Fabric IQ `iqnpl_ontology` via the verified `fabric_iq_preview` tool
(`docs/verified-capabilities.md` §2a). The model is a **swappable deployment-name string** — swapping
`gpt-5.4` ↔ `gpt-5.4-mini` is a config change with no code rewrite (Art. III); weights are never touched
(Art. II).

```
agent/
  agent.yaml               # hosted-agent manifest (model = ${FOUNDRY_MODEL_DEPLOYMENT_NAME}, swappable)
  harness.py               # load_config() + create/invoke/delete a Foundry agent version; captures metrics
  .agent_configs/
    baseline/
      instructions.md      # water-analyst persona  -> Instruction-tuning target
      tools.json           # fabric_iq_preview -> iqnpl_ontology -> Tool-optimization target (descriptions only)
      skills/
        SKILL.md           # investigation skill body -> Skill-improvement target
```

## Grounding (verified)
`tools.json` declares one `fabric_iq_preview` tool whose `server_url` is the ontology MCP endpoint:
`.../v1/mcp/dataPlane/workspaces/${FABRIC_WORKSPACE_ID}/items/${FABRIC_ONTOLOGY_ITEM_ID}/ontologyEndpoint`.
The tool **requires** a `project_connection_id` — a **Fabric IQ (OneLake Catalog)** connection created once
in the Foundry portal (managed OAuth; needs *Foundry Project Manager*). Its id comes from
`FABRIC_IQ_PROJECT_CONNECTION_ID` in `.env` (never committed). At runtime the model emits a tool call, Fabric
IQ runs NL2Ontology over the bound OneLake data in the signed-in user's context, and returns the answer.

## Non-parametric optimization (why this layout)
An agent is **optimizer-ready** when it loads these files via `load_config()`, so the *same code* runs with
or without the Agent Optimizer (Phase 6). The optimizer changes **only text/config** — instructions
(`instructions.md`), tool **descriptions** (`tools.json`), and skill **bodies** (`skills/`) — never weights
(Art. II) and never business logic (Art. III). Per **Art. IV** no table/column/SQL is baked into any of
these files; the agent reaches all semantics through the ontology tool.

## Usage
```bash
pip install -r requirements.txt      # needs azure-ai-projects>=2.2.0
az login                             # delegated identity (no secrets stored)
cp .env.example .env                 # fill FOUNDRY_PROJECT_ENDPOINT, FABRIC_IQ_PROJECT_CONNECTION_ID, ...

# One-off smoke test (swap the model freely):
python agent/harness.py --model gpt-5.4      --prompt "How many monitored sites are active?"
python agent/harness.py --model gpt-5.4-mini --prompt "How many monitored sites are active?"
```

`harness.py` returns, per invocation: the answer, the Fabric IQ tool calls (groundedness/traversal
evidence), input/output tokens, latency, and the config hash (fairness fingerprint). The evaluation
framework in `eval/` drives this harness across the question set.
