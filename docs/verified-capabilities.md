# Verified Capabilities — Phase 0 Feasibility Gate

> **Issue:** #8 (EPIC B #2) · **Status:** Phase 0 GATE · **Verification date:** 2026-07-03
> **Author:** Phase 0 child session · **Governs:** Constitution Art. I (Accuracy & Verification),
> Art. II (Non-Parametric Integrity), Art. XIII (Epic→Issue→PR).

## Purpose & method
This note validates every load-bearing tooling claim behind the initiative against **primary Microsoft
sources only** — Microsoft Learn, official `github.com/microsoft` repos, and Microsoft Research/product
blogs. LLM/search summaries were treated as leads, not proof; each fact below was confirmed by fetching
the actual documentation page. The source material (Gemini-generated PDF) is **unverified** and several
of its specifics were found to be inaccurate — see [Corrections to the source PDF](#corrections-to-the-source-pdf).

**Status legend:** `Verified-GA` = generally available · `Verified-Preview` = real, documented, in
public preview · `Gated` = real but requires allow-list/approval · `Unverified` = could not confirm
against a primary source (fallback documented).

All pages carry a `ms.date` / `updated_at` in mid-2026 and are current as of the verification date above.

---

## 1. Fabric IQ Ontology (preview)

**Status: `Verified-Preview`**

Fabric IQ is part of Microsoft IQ and ships as an **IQ (preview) workload** in Microsoft Fabric. The
**ontology (preview)** item is the semantic layer over OneLake: it defines *entity types*, *properties*,
*relationships* (typed, directional, with cardinality/attributes), plus constraints/rules, then binds
those definitions to real data.

**Primary sources (accessed 2026-07-03):**
- What is Fabric IQ? — https://learn.microsoft.com/en-us/fabric/iq/overview *(updated 2026-06-05)*
- What Is Ontology (Preview)? — https://learn.microsoft.com/en-us/fabric/iq/ontology/overview *(updated 2026-05-14)*
- Bind Data — https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-bind-data *(ms.date 2026-04-21)*
- Ontology required tenant settings — https://learn.microsoft.com/en-us/fabric/iq/ontology/overview-tenant-settings *(ms.date 2026-04-30)*

### 1a. Authoring entities / relationships / data bindings over OneLake — Verified
- **Entity type**: reusable logical model of a concept (name, identifiers, properties, constraints).
  **Entity instance**: a concrete occurrence populated from bindings, with source lineage + validity.
- **Relationship**: typed, directional link with attributes (e.g. `distance`, `confidence`,
  `effectiveAt`) and cardinality rules — enables graph traversal without custom joins.
- **Data binding** connects definitions to concrete OneLake data: **Lakehouse tables** (static/business
  entities), **Eventhouse streams** (time-series, columnar format), and **Power BI semantic models**.
  Binding maps columns→properties, defines the **entity type key**, and maps keys→relationships. It does
  **not copy** data. Upstream changes require a **manual graph refresh** before they appear.
- **Binding limitations** (verified, important for Phase 3/4): Lakehouse tables must be **managed**, must
  **not** have OneLake security enabled, and must **not** have column mapping enabled.
- **Querying**: an **NL2Ontology** layer converts natural-language questions into structured queries,
  dispatching to the most efficient engine (**GQL** for Graph in Fabric, **KQL** for Eventhouse). The
  graph feature **requires Graph in Microsoft Fabric to be enabled at the tenant**.

### 1b. How the ontology is exposed to an agent — **RESOLVED: two real mechanisms**
The Constitution/plan open question ("MCP endpoint vs native Foundry connector") is resolved: **both
exist and are documented.** They are complementary, not mutually exclusive.

1. **Native Foundry IQ connector (recommended for hosted Foundry agents).** In the Foundry portal you
   create a **Knowledge base**, choose knowledge type **"Fabric IQ"**, and pick the ontology item via
   the embedded **OneLake catalog**. You then attach that knowledge base to an agent under its
   **Knowledge** section. This is a first-class native connector — **not** MCP.
   - Source: *Create an Ontology Agent with Foundry IQ* —
     https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-agent-foundry-iq *(updated 2026-06-02)*
2. **MCP server endpoint (pro-code / VS Code / Copilot Studio / any MCP client).** The ontology can act
   as an **MCP server**. The endpoint is derived from the item URL:
   `https://api.fabric.microsoft.com/v1/mcp/dataPlane/workspaces/<workspace-ID>/items/<ontology-item-ID>/ontologyEndpoint`
   and registered as an HTTP MCP server (e.g. in `.vscode/mcp.json`).
   - Source: *Use Ontology MCP Server* —
     https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-use-ontology-mcp-server *(updated 2026-06-30)*

> **Decision for this project:** use the **native Foundry IQ "Fabric IQ" knowledge source** as the
> primary path (it is the documented way to ground a *hosted Foundry agent*, which is what the optimizer
> targets). Keep the **MCP endpoint** as the documented alternative for non-Foundry / editor-based demos.

### 1c. Entra ID auth model & required permissions — Verified (delegated) / partial gap (service principal)
- **Access is identity-based (delegated).** The Foundry IQ flow states only ontology items **your
  identity can read** are visible in the OneLake catalog; the same signed-in identity must have access to
  **both** the Foundry project and the Fabric workspace. The MCP flow authenticates via **interactive
  sign-in** ("Allow" + credentials) in the client.
- **Capacity/licensing**: a **paid F2+ Fabric capacity** (or **Power BI Premium P1+** with Fabric
  enabled). MCP server usage lists the same requirement.
- **Tenant settings** (Fabric admin): **"Enable Ontology item (preview)"** is required; the **Graph**
  tenant setting is required for the graph feature; **Fabric data agent** / **operations agent** tenant
  settings are required only if consuming the ontology through those agents.
- **Gap:** the specific claim in the source PDF of an **Entra app registration with `Item.Execute.All` /
  `Item.Read.All` scopes** is **not corroborated** on these preview pages — documented access is
  delegated user identity via the OneLake catalog, not a spelled-out service-principal scope set.
  **Fallback:** proceed with **delegated user identity** (as documented) for the demo; treat any
  service-principal / app-registration scope list as **Unverified** and re-verify against Fabric REST API
  / OneLake security docs before it enters the public article.

---

## 2. Foundry Agent Service — grounding an agent in Fabric IQ & frozen weights

**Status: `Verified-Preview`** (Fabric IQ knowledge grounding is preview; hosted agents are a Foundry
Agent Service capability)

**Primary sources (accessed 2026-07-03):**
- *Create an Ontology Agent with Foundry IQ* — https://learn.microsoft.com/en-us/fabric/iq/ontology/how-to-create-agent-foundry-iq
- *Agent optimizer overview* (hosted-agent model/config context) — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview

### 2a. Wiring the Fabric IQ tool/connection to a hosted agent — Verified
Documented end-to-end flow: **New agent → pick a model deployment → system prompt → Knowledge →
+ Add knowledge → select the Fabric IQ knowledge base**. The agent then routes relevant questions to the
ontology automatically and can be exercised from the built-in **Chat** pane or via the Foundry APIs. This
confirms the semantic-contract narrative: business vocabulary lives in the ontology, the agent consumes
it as governed knowledge (Constitution Art. IV).

### 2b. Keeping model weights frozen (config) — Verified by construction (supports Art. II)
- A Foundry hosted agent references a **model *deployment*** (a config value), not trainable weights.
  Swapping the model is a config/deployment change — no code rewrite (supports Art. III swappability).
- The optimization path (§3) changes **only text/config** — instructions, skills, tool descriptions, and
  **model *selection*** — and **never** fine-tunes or updates weights. There is no weight-update step
  anywhere in the documented optimizer loop. This directly satisfies **Non-Parametric Integrity**.

---

## 3. Foundry Agent Optimizer (azd extension)

**Status: `Gated` (Verified-Preview + allow-list required)**

The optimizer is real, documented, and in **public preview**, **but subscription access is gated**: *"Your
Azure subscription must be on the allow list for the agent optimizer. Contact your Microsoft
representative to request access."* This is the single biggest Phase 0 risk and drives the fallback in §4.

**Primary sources (accessed 2026-07-03, all `ms.date` 2026-05-18 to 2026-06-22):**
- Overview — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview
- Optimize targets — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/optimize-agent-targets
- Create dataset/evaluators — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/create-optimizer-dataset
- Quickstart — https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-optimize-hosted-agent

### 3a. Real extension & commands — Verified
- **Extension (corrected):** `azd ext install microsoft.foundry` (needs `0.1.40-preview`+ of the
  `azure.ai.agents` dependency). Requires **azd CLI** + **Azure CLI**.
- **Commands (verified):**
  - `azd ai agent init -m <manifest-url> .` — scaffold from a manifest; generates `agent.yaml`,
    `.agent_configs/baseline/`, the eval dataset, and infra files.
  - `azd provision` → `azd deploy` → `azd ai agent invoke "<prompt>"` — provision/deploy/smoke-test.
  - `azd ai agent eval generate` — auto-detects the agent, generates a dataset + adaptive evaluators,
    and writes a runnable **`eval.yaml`**.
  - `azd ai agent optimize` (auto-detects `eval.yaml`) or `azd ai agent optimize --config eval.yaml`.
    Flags: `--agent`, `--eval-model`, `--optimize-model`.
  - `azd ai agent optimize apply --candidate <cand_id>` then `azd deploy` — promote the winner.
- **Loop:** evaluate baseline → generate candidates → evaluate candidates → rank by composite **score
  (0.0–1.0)**, best marked ★ → deploy winner. Runs in the cloud, ~5–20 min.
- **Availability:** all regions where hosted agents are available **except Norway East**; supported for
  hosted agents using the **Responses** protocol.

### 3b. Optimization targets — Verified (all four are real)
Targets auto-activate from the baseline config + `eval.yaml`:
| Target | Activates when baseline has | What it changes |
| --- | --- | --- |
| **Instruction tuning** | `instructions.md` | Rewrites the system prompt |
| **Skill improvement** | `skills/` (each `SKILL.md`) | Refines skill **bodies**; descriptions unchanged; loaded via `load_config()` |
| **Tool optimization** | `tools.json` | Improves tool/param **descriptions** only (never types/defaults/required) |
| **Model selection** | `optimization_config.model_search_space` in `eval.yaml` | Scores agent across multiple model deployments for quality/cost trade-off |

An agent is **"optimizer-ready"** when it calls **`load_config()`** (resolves inline JSON → resolver API →
local `.agent_configs/` → `None`), so the same code runs with or without optimization.

### 3c. Real `eval.yaml` shape — Verified (corrects the PDF's guessed keys)
```yaml
# eval.yaml
options:
  eval_model: gpt-4.1-mini          # scores responses; any chat-completion model
  optimization_model: gpt-5.1       # REQUIRED; must be from the supported list below
  optimization_config:
    model_search_space:             # presence enables the model-selection target
      - gpt-4.1
      - gpt-4.1-mini
      - gpt-4o
```
- **Two models:** `eval_model` (`--eval-model`, binary score per task/criterion) and
  `optimization_model` (`--optimize-model`, generates candidates). `optimization_model` is **required**.
- **Supported `optimization_model` list (verified):** `gpt-5`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4`,
  `gpt-5.5`, `DeepSeek-V4-Pro`, `DeepSeek-V-3.2`.
- **Dataset:** default built-in = **3 general coding tasks + 25 criteria**; custom datasets are **JSONL**.
- **Score interpretation (verified):** <0.03 noise · 0.03–0.10 moderate · 0.10–0.20 significant · >0.20 major.
- ⚠️ **Every dataset task invokes the agent**, executing any real tool calls — use test endpoints/mocks
  to avoid charges/state mutation (relevant to Art. V synthetic-fixtures discipline).

---

## 4. SkillOpt (Microsoft Research) — conceptual anchor & custom-loop fallback

**Status: `Verified-GA` (open-source; repo, paper, and PyPI package all confirmed real)**

**Primary sources (accessed 2026-07-03):**
- Repo — https://github.com/microsoft/SkillOpt (MIT license; PyPI `skillopt`; Python 3.10+)
- Research blog — https://www.microsoft.com/en-us/research/blog/skillopt-agent-skills-as-trainable-parameters/ *(2026-06)*
- Paper — *"SkillOpt: Executive Strategy for Self-Evolving Agent Skills"*, arXiv:2605.23904 /
  https://www.microsoft.com/en-us/research/publication/skillopt-executive-strategy-for-self-evolving-agent-skills/

**Accurate summary:** SkillOpt treats an agent **skill file as a trainable parameter outside a frozen
target model**, turning skill authoring into a controlled optimization loop — rollout → reflect →
bounded add/delete/replace edits (a textual "learning rate") → **held-out validation gate** →
best-version selection, with a rejected-edit buffer and epoch-wise slow/meta updates. Reported best or
tied-best across **6 benchmarks, 7 target models, 3 execution modes (52/52 cells)** with **no weight
updates**. Releases as of verification: **v0.1.0 (2026-06-02)** and **v0.2.0 (2026-07-02)** (adds
"SkillOpt-Sleep"; backends for Claude/Codex/Copilot/Devin/OpenClaw; multi-backend OpenAI/Azure/Claude/
Qwen/MiniMax).

**Role in this project:** the **conceptual anchor** for "text-space, non-parametric optimization" and the
**fallback custom loop** if Agent Optimizer allow-list access (§3) is not granted. SkillOpt is a
Microsoft Research artifact — attribute it correctly per Constitution Art. VII.2.

---

## Corrections to the source PDF
Per Art. I.5, inaccuracies in the Gemini-generated source are corrected here:

1. **`fabric_iq_connection` tool type — inaccurate.** No such single tool. The real mechanisms are
   (a) the native **Foundry IQ "Fabric IQ" knowledge source/base** (via OneLake catalog) and
   (b) the **ontology MCP server** endpoint.
2. **"MCP vs native connector" — resolved as both.** Native Foundry IQ connector is the recommended path
   for a hosted Foundry agent; MCP is the pro-code/editor alternative.
3. **azd extension name/flags — corrected.** The extension is **`microsoft.foundry`**
   (`azd ext install microsoft.foundry`); the verified commands are `azd ai agent init` /
   `eval generate` / `optimize` / `optimize apply` / `invoke` (not the PDF's guessed `azd ai agent`
   flag set).
4. **`model_search` YAML key — corrected.** The real key is
   **`options.optimization_config.model_search_space`**.
5. **Entra `Item.Execute.All` / `Item.Read.All` app-reg scopes — unverified.** Documented access is
   **delegated user identity** via the OneLake catalog / interactive sign-in; the specific
   service-principal scope list is not confirmed on the preview pages (see §1c fallback).

## Gaps, risks & fallbacks (summary)
| # | Gap / risk | Impact | Fallback |
| --- | --- | --- | --- |
| G1 | **Agent Optimizer is allow-list gated** (§3) | May block the native optimization demo | Request access via Microsoft rep now; else use **SkillOpt-style custom Python loop** (§4) to demonstrate the same non-parametric loop |
| G2 | **Service-principal Entra scopes for Fabric IQ undocumented** (§1c) | Automation/CI auth uncertain | Use **delegated user identity** as documented; re-verify SP scopes before publication |
| G3 | Ontology **binding limitations** (managed tables, no OneLake security, no column mapping) | Constrains fixture design | Design Phase 3 synthetic fixtures to comply from the start |
| G4 | Graph feature needs **tenant Graph setting**; upstream data needs **manual refresh** | Setup/latency friction | Document as prerequisites; script refresh in the repo |

## Gate decision
Phases 1+ may proceed **once this note is merged** (Art. XIII). All four capabilities are real and
primary-sourced. The **only hard dependency** is **G1 (optimizer allow-list)** — the plan must carry the
**SkillOpt custom-loop fallback** as a first-class alternative so the non-parametric narrative holds even
without allow-list access.
