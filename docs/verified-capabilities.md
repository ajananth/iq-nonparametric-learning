# Verified Capabilities — Phase 0 Feasibility Gate

> **Issue:** #8 (EPIC B, #2) · **Status:** Phase 0 GATE · **Verification date:** **2026-07-03**
> **Author:** Phase 0 child session · **Governs:** Constitution Art. I (Accuracy & Verification),
> Art. II (Non-Parametric Integrity), Art. III (Model Independence), Art. XIII (Epic→Issue→PR).

## Purpose & method
This note validates every load-bearing tooling claim behind the initiative against **primary Microsoft
sources only** — Microsoft Learn, official `github.com/microsoft` and `github.com/MicrosoftDocs` repos,
and Microsoft Research/product blogs. LLM/search summaries were treated as leads, **not** proof; each fact
below was confirmed by fetching the actual documentation page on the verification date. The source material
(Gemini-generated PDF) is **unverified** and several of its specifics were found to be inaccurate — see
[Corrections to the source PDF](#corrections-to-the-source-pdf).

**Status legend:** `Verified-GA` = generally available · `Verified-Preview` = real, documented, in public
preview (no SLA; may change) · `Gated` = real but requires an allow-list/approval beyond preview signup ·
`Unverified` = could not confirm against a primary source (fallback documented).

All pages carry a `ms.date` / `updated_at` in mid-2026 and are current as of the verification date above.

---

## 1. Fabric IQ Ontology (preview)

**Status: `Verified-Preview`**

The **ontology (preview)** item is the semantic layer of the **Fabric IQ (preview) workload** over OneLake.
It models *entity types*, *properties*, and *relationships* (typed, directional, with cardinality and
attributes), plus constraints/rules, and binds those definitions to real data.

**Primary sources (accessed 2026-07-03):**
- What Is Ontology (Preview)? — https://learn.microsoft.com/en-us/fabric/iq/ontology/overview *(updated 2026-05-14)*
- Bind Data — https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-bind-data *(updated 2026-06-22)*
- Ontology required tenant settings — https://learn.microsoft.com/en-us/fabric/iq/ontology/overview-tenant-settings *(updated 2026-06-22)*
- Use Ontology MCP Server — https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-mcp-server *(updated 2026-06-30)*

### 1a. Authoring entities / relationships / data bindings over OneLake — Verified
- **Entity type**: reusable logical model of a concept (name, identifiers, properties, constraints).
  **Entity instance**: a concrete occurrence populated from bindings, carrying source lineage and validity.
- **Relationship**: typed, directional link with attributes (e.g. `distance`, `confidence`, `effectiveAt`)
  and cardinality rules — enables graph traversal without custom joins.
- **Data binding** connects definitions to concrete OneLake data **without copying it**: **Lakehouse tables**
  (static/business entities), **Eventhouse streams** (time-series, *columnar* format), and **Power BI semantic
  models**. Binding maps columns→properties, defines the **entity type key**, and maps keys→relationships.
- **Binding limitations** (verified — important for Phase 3/4 fixtures): Lakehouse tables must be **managed**,
  must **not** have OneLake security enabled, and must **not** have column mapping enabled. Upstream changes
  (new rows) require a **manual graph refresh** before they appear.
- **Querying**: a **Natural Language → Ontology (NL2Ontology)** layer converts business-term questions into
  structured queries, dispatching to the most efficient engine (**GQL** for Graph in Fabric, **KQL** for
  Eventhouse). The graph feature **requires Graph in Microsoft Fabric to be enabled at the tenant**.
- Supports our water-utilities model (WaterSource/Plant/MonitoringStation/Metric with monitors/supplies/records
  relationships, telemetry bound from an Eventhouse) and satisfies **Art. IV** (schema + vocabulary live in the
  ontology, not in prompts).

### 1b. How the ontology is exposed to an agent — **RESOLVED (the key open question)**
The plan's open question ("MCP endpoint **vs** native Foundry connector") rested on a **false dichotomy**.
There are **three documented, complementary paths**, and the flagship one is *native tool implemented over MCP*:

1. **Foundry IQ knowledge base (native, portal).** In the Foundry portal: **Knowledge → Knowledge bases →
   + New knowledge base → knowledge type "Fabric IQ" → OneLake catalog picker → select the ontology item**,
   then attach the knowledge base to an agent. See §2. *(fabric/iq/ontology/how-to-create-agent-foundry-iq)*
2. **`fabric_iq_preview` server-side tool (native tool, MCP transport).** Foundry Agent Service registers the
   ontology as a first-class tool whose `server_url` is a **Fabric IQ MCP endpoint** — i.e. the native tool is
   **built on MCP**, not an alternative to it. See §2. *(foundry/agents/how-to/tools/fabric-iq)*
3. **Raw ontology MCP server (any MCP client).** The ontology is directly consumable as an MCP server at
   `https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/<workspace-ID>/items/<ontology-item-ID>/ontologyEndpoint`
   (e.g. registered in `.vscode/mcp.json` as an HTTP server). *(fabric/iq/ontology/how-to-use-ontology-mcp-server)*

> **Decision for this project:** use the **`fabric_iq_preview` tool** (path 2) as the primary way to ground the
> **hosted Foundry agent** — it is the path the Agent Optimizer and the model-swappability story build on. The
> **knowledge-base** path (1) is the equivalent portal experience; the **raw MCP endpoint** (3) is the
> alternative for non-Foundry / editor-based demos.

### 1c. Entra ID auth model & required permissions — Verified (delegated) / gap on SP scopes
- **Access is identity-based (delegated / user-identity passthrough).** The Foundry IQ knowledge-base flow shows
  only ontology items **your identity can read**, and requires the same signed-in identity to have access to
  **both** the Foundry project and the Fabric workspace. The `fabric_iq_preview` tool runs **all requests in the
  context of the signed-in user**, honoring Fabric permissions/governance, and authenticates via **BYO Entra app
  + managed OAuth** (Foundry API token scope `https://ai.azure.com/.default`). *(how-to-create-agent-foundry-iq, tools/fabric-iq)*
- **Azure RBAC (for the `fabric_iq_preview` tool):** **Foundry User** on the project (developer identity, agent
  runtime identity, and any user identity in OAuth flows) + **Foundry Project Manager** (to create the Fabric IQ
  connection). Invoking users also need a **Microsoft Fabric license** with access to the queried items. *(tools/fabric-iq)*
- **Capacity/licensing:** paid **F2+ Fabric capacity** (or **Power BI Premium P1+** with Fabric enabled). *(how-to-use-ontology-mcp-server)*
- **Tenant settings (Fabric admin):** **"Enable Ontology item (preview)"** is required; the **Graph** tenant
  setting is required for the graph feature; **Fabric data agent** / **operations agent** tenant settings are
  required only if consuming the ontology through those agents. *(overview-tenant-settings)*
- **Gap / correction:** the source PDF's specific **`Item.Execute.All` / `Item.Read.All`** Entra app-registration
  scopes are **not corroborated** on these preview pages — documented access is delegated user identity + a BYO
  Entra app via managed OAuth, not a spelled-out service-principal scope set. **Fallback:** proceed with
  **delegated user identity** (as documented) for the demo; treat any service-principal scope list as
  **Unverified** and re-confirm against the BYO Entra-app registration flow / Fabric REST API docs before it
  enters the public article.

---

## 2. Foundry Agent Service — grounding an agent in Fabric IQ & frozen weights

**Status: `Verified-Preview`** (Fabric IQ grounding is preview; hosted agents are a Foundry Agent Service capability)

**Primary sources (accessed 2026-07-03):**
- Connect agents to Microsoft Fabric with Fabric IQ (preview) — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/tools/fabric-iq *(updated 2026-07-01)*
- Create an Ontology Agent with Foundry IQ — https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-agent-foundry-iq *(updated 2026-06-02)*

### 2a. Attaching the Fabric IQ tool/connection to a hosted agent — Verified
- **Tool type: `fabric_iq_preview`** (Python/JS/.NET SDK class `FabricIQPreviewTool`). Requires
  `azure-ai-projects >= 2.2.0`. SDK/interface support: Python ✔, C# ✔, JavaScript ✔, REST ✔ (Java —); works with
  Basic and Standard agent setup.
- The agent is defined with a model deployment + instructions + the tool, e.g.
  `PromptAgentDefinition(model=<deployment-name>, instructions=..., tools=[FabricIQPreviewTool(project_connection_id=..., require_approval=...)])`,
  created via `project_client.agents.create_version(...)`. REST tool block:
  `{ "type": "fabric_iq_preview", "project_connection_id": ..., "server_label": ..., "server_url": ... }`.
- **`server_url` patterns** (the value is a Fabric IQ **MCP** endpoint; `{host}` ≈ `api.fabric.microsoft.com`):
  - **Ontology:** `https://{host}/v1/mcp/dataPlane/workspaces/{workspaceId}/items/{itemId}/ontologyEndpoint`
  - **Data agent:** `https://{host}/v1/mcp/workspaces/{workspaceId}/dataagents/{dataAgentId}/agent`
  - **Power BI semantic model:** `https://{host}/v1/mcp/fabricaihub/integrations/m365`
- At runtime the model emits a tool call to `fabric_iq_preview`; Fabric IQ routes by item type (NL2Ontology for
  the ontology), retrieves from bound OneLake sources, synthesizes, and returns the answer to the agent — all in
  the signed-in user's context.
- **Portal equivalent (Foundry IQ knowledge base):** New agent → pick model deployment → system prompt →
  **Knowledge → + Add knowledge → select the "Fabric IQ" knowledge base** → chat from the built-in **Chat** pane.
  *(how-to-create-agent-foundry-iq)*
- **Preview caveat (from the page):** connecting to Fabric IQ may incur cost and may send data outside the Azure
  compliance boundary — must be reviewed against **Art. VI/VII** before any real-data wiring.

### 2b. Keeping model weights frozen (config) — Verified by construction (supports Art. II & III)
- A hosted agent references a **model *deployment* by name** (a config string), not trainable weights. Swapping
  the model is a config/deployment change — **no code rewrite** (Art. III swappability).
- The optimization path (§3) changes **only text/config** — instructions, skills, tool descriptions, and **model
  *selection*** — and **never** fine-tunes or updates weights. There is no weight-update step anywhere in the
  documented optimizer loop. This directly satisfies **Non-Parametric Integrity**.

---

## 3. Foundry Agent Optimizer (azd extension)

**Status: `Gated` (Verified-Preview + subscription allow-list required)**

The optimizer is real, documented, and in **limited public preview**, **but subscription access is gated**:
*"Your Azure subscription must be on the allow list for the agent optimizer. Contact your Microsoft
representative to request access."* (A gated `optimize` call returns **403**.) This is the single biggest Phase 0
risk and drives the fallback in §4.

**Primary sources (accessed 2026-07-03, `ms.date` 2026-05-18 unless noted):**
- Overview — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview
- Optimize targets — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/optimize-agent-targets
- Create dataset/evaluators — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/create-optimizer-dataset
- Quickstart — https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-optimize-hosted-agent
- azd agent extension — https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension *(ms.date 2025-12-11)*

### 3a. Real extension & commands — Verified
- **Extension: `azure.ai.agents`**, installed with **`azd ext install azure.ai.agents`** (equivalently
  `azd extension install azure.ai.agents`; auto-installs on first `azd ai agent ...` use). Requires **azd**
  1.21.3+ and **Azure CLI** (`az login` + `azd auth login`).
- **Commands (verified):**
  - `azd ai agent init -m <agent-definition-or-manifest-url> [.] [-p <project-resource-id>]` — scaffold; generates
    `agent.yaml`, `.agent_configs/baseline/`, dataset, and IaC (`infra/`, `azure.yaml`).
  - `azd provision` → `azd deploy` (or `azd up`) → `azd ai agent invoke "<prompt>"` — provision/deploy/smoke-test.
  - `azd ai agent eval init [--gen-instruction "..." | --dataset <jsonl>] [--eval-model <m>] [--max-samples N]` —
    generate a domain-tuned `eval.yaml`, dataset, and evaluators. (`azd ai agent eval run` runs the eval suite.)
  - `azd ai agent optimize [--config eval.yaml] [--agent <name>] [--eval-model <m>] [--optimize-model <m>] [--watch]`
    — auto-detects `eval.yaml`; runs the closed-loop optimization (~5–20 min).
  - `azd ai agent optimize apply --candidate <id>` → `azd deploy` (recommended promote), or
    `azd ai agent optimize deploy --candidate <id>` (direct A/B), or `azd ai agent optimize cancel <id>`.
- **Loop:** evaluate baseline → generate candidates → evaluate candidates → rank by composite **score (0.0–1.0)**,
  best marked ★ → deploy the winner. Runs in the cloud.

### 3b. Optimization targets — Verified (all four are real)
Targets auto-activate from the baseline config + `eval.yaml`. An agent is **"optimizer-ready"** when it calls
**`load_config()`**, so the same code runs with or without optimization.

| Target | Activates when baseline has | What it changes |
| --- | --- | --- |
| **Instruction tuning** | `instructions.md` | Rewrites the system prompt |
| **Skill improvement** | `skills/` (each `SKILL.md`) | Refines skill **bodies** (descriptions unchanged); loaded via `load_config()`; open **Agent Skills** format (agentskills.io) |
| **Tool optimization** | `tools.json` | Improves tool/parameter **descriptions** only (never types/defaults/required) |
| **Model selection** | `options.optimization_config.model` list in `eval.yaml` | Scores the agent across multiple model deployments for quality/cost trade-off |

### 3c. Real `eval.yaml` shape — Verified (corrects the PDF's guessed keys)
```yaml
# eval.yaml
agent:
  name: my-agent                 # or resolved from agent.yaml / the --agent flag
dataset_file: ./eval.jsonl
evaluators:
  - builtin.task_adherence       # also e.g. builtin.intent_resolution
options:
  eval_model: gpt-4.1-mini       # scores responses; any deployed chat-completion model
  optimization_model: gpt-5.1    # REQUIRED ("reflection" model); generates candidates
  max_iterations: 5              # default 4
  optimization_config:
    model:                       # presence enables the model-selection target
      - gpt-4.1
      - gpt-4.1-mini
      - gpt-4o
```
- **Two models:** `eval_model` (`--eval-model`) scores each task/criterion (binary 0/1 for `builtin.task_adherence`);
  `optimization_model` (`--optimize-model`) generates candidates and is **required** (missing → API error).
- **Supported `optimization_model` values (verified):** **`gpt-5`, `gpt-5.1`, `gpt-5.3`**.
- **Dataset:** default built-in = **3 general coding tasks + 25 criteria**; custom datasets are **JSONL**, one
  task per line: `{"name","prompt","criteria":[{"name","instruction"}], "groundTruth"?}`.
- **Score interpretation (verified):** <0.03 noise · 0.03–0.10 moderate (worth deploying) · 0.10–0.20 significant ·
  >0.20 major.
- ⚠️ **Every dataset task invokes the agent**, executing any real tool calls — use test endpoints/mocks to avoid
  charges/state mutation (relevant to **Art. V** synthetic-fixtures discipline). If the eval model isn't deployed,
  **all scores silently return 0**.

---

## 4. SkillOpt (Microsoft Research) — conceptual anchor & custom-loop fallback

**Status: `Verified-GA`** (open-source; repo, paper, and PyPI package all confirmed real)

**Primary sources (accessed 2026-07-03):**
- Repo — https://github.com/microsoft/SkillOpt (MIT license; PyPI `skillopt`; Python 3.10+)
- Research blog — https://www.microsoft.com/en-us/research/blog/skillopt-agent-skills-as-trainable-parameters/ *(2026-06)*
- Paper — *"SkillOpt: Executive Strategy for Self-Evolving Agent Skills"*, arXiv:2605.23904 /
  https://www.microsoft.com/en-us/research/publication/skillopt-executive-strategy-for-self-evolving-agent-skills/

**Accurate summary:** SkillOpt treats an agent **skill file as a trainable parameter outside a frozen target
model**, turning skill authoring into a controlled optimization loop — rollout → reflect (separate optimizer
model) → bounded add/delete/replace edits clipped by a **textual "learning rate"** → **strict held-out validation
gate** (adopt only if strictly better) → best-version selection, with a **rejected-edit buffer** as negative
feedback and epoch-wise slow/meta updates. Reported best or tied-best across **6 benchmarks, 7 target models, 3
execution modes (52/52 evaluation cells)**, with **no weight updates**; multi-backend (OpenAI / Azure / Claude /
Qwen / MiniMax). Releases as of verification: **v0.1.0 (2026-06-02)** and **v0.2.0 (2026-07-02)** (adds
"SkillOpt-Sleep"; Claude/Codex/Copilot/Devin/OpenClaw backends).

**Role in this project:** the **conceptual anchor** for "text-space, non-parametric optimization" and the
**fallback custom loop** if Agent Optimizer allow-list access (§3) is not granted. It targets the same text-space
artifacts (`instructions.md`, skills, tool descriptions). Attribute correctly to Microsoft Research (**Art. VII.2**).

---

## Corrections to the source PDF
Per **Art. I.5**, inaccuracies in the Gemini-generated source are corrected here:

1. **`fabric_iq_connection` tool type — inaccurate.** No such single tool. The real Foundry tool type is
   **`fabric_iq_preview`** (`FabricIQPreviewTool`).
2. **"MCP vs native connector" — false dichotomy; resolved as both.** The flagship native tool (`fabric_iq_preview`)
   is itself **built on MCP** (its `server_url` is a Fabric IQ MCP endpoint). There is also a portal **Foundry IQ
   knowledge base** path and a **raw ontology MCP endpoint** for any MCP client.
3. **azd extension name — corrected.** The extension is **`azure.ai.agents`** (`azd ext install azure.ai.agents`),
   **not** `microsoft.foundry`.
4. **Optimizer eval command — corrected.** Dataset generation is **`azd ai agent eval init`**, not `eval generate`.
5. **Model-selection YAML key — corrected.** The real key is **`options.optimization_config.model`** (a list of
   deployment names), **not** `model_search` / `model_search_space`.
6. **Supported optimization models — corrected.** Primary docs list **`gpt-5`, `gpt-5.1`, `gpt-5.3`** for
   `optimization_model` (any deployed chat model may serve as `eval_model`). Do not publish a wider list as fact.
7. **Entra `Item.Execute.All` / `Item.Read.All` scopes — unverified.** Documented access is **delegated user
   identity** + a **BYO Entra app via managed OAuth**, with RBAC **Foundry User** + **Foundry Project Manager**
   (see §1c/§2a). Do not publish those scope strings as fact until confirmed in the app-registration flow.
8. **Optimizer availability — clarified.** It is **not openly available**: it is a **limited preview gated by a
   subscription allow-list** ("contact your Microsoft representative"; 403 otherwise).

## Gaps, risks & fallbacks (summary)
| # | Gap / risk | Impact | Fallback |
| --- | --- | --- | --- |
| G1 | **Agent Optimizer is allow-list gated** (§3) | May block the native optimization demo | Request access via Microsoft rep now; else use a **SkillOpt-style custom Python loop** (§4) to demonstrate the same non-parametric loop against `instructions.md` / skills / tool descriptions |
| G2 | **Service-principal Entra scopes for Fabric IQ undocumented** (§1c) | Automation/CI (non-interactive) auth uncertain | Use **delegated user identity** as documented; re-verify SP scopes before publication |
| G3 | Ontology **binding limitations** (managed tables, no OneLake security, no column mapping) | Constrains fixture design | Design Phase 3 synthetic fixtures to comply from the start |
| G4 | Graph feature needs **tenant Graph setting**; upstream data needs **manual refresh** | Setup/latency friction | Document as prerequisites; script the refresh in the repo |
| G5 | Fabric IQ preview may **incur cost / send data outside the Azure compliance boundary** (§2a) | Compliance (Art. VI/VII) | Gate real-data wiring behind explicit approval; keep synthetic fixtures for the public demo |

## Gate decision
Phase 0's verification objective is met: every load-bearing claim now carries a primary-source citation and a
stated status. All four capabilities are real; the **only hard dependency for a fully-native build is the Agent
Optimizer allow-list (G1)**, for which a documented SkillOpt-style fallback exists. **Recommendation to the master
session:** (a) request allow-list access early, and (b) design the Phase 6 optimization loop so the SkillOpt-style
path is a drop-in if access is delayed. Per **Art. XIII**, no Phase 1+ build work should begin until this note is
merged.
