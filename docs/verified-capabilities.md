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
- **Capacity/licensing:** paid **F2+ Fabric capacity** (or **Power BI Premium per-capacity P1+** with **Microsoft Fabric enabled**). *(how-to-use-ontology-mcp-server)*
  > **§1c re-verification note (Phase 2, #15, re-checked 2026-07-03):** The Phase 2 SME asserted that
  > **P1+/Premium does *not* support ontologies** and requested this line be corrected to *F2+ only*. Per
  > **Art. I**, the claim was re-checked against the primary source before changing anything. The current
  > **Use Ontology MCP Server** prerequisites (Microsoft Learn, `updated_at` **2026-06-30**) still explicitly
  > list *"A paid **F2** or higher Fabric capacity, **or** a **Power BI Premium per capacity (P1 or higher)**
  > capacity with **Microsoft Fabric enabled**"*. The **Features by SKU and Capacity** feature-parity list
  > (`ms.date` 2026-06-30) does **not** carve ontology out as F-SKU-only. Because the primary source
  > **confirms P1+ (with Fabric enabled)**, the F2-only correction was **not forced** — primary-source
  > verification decides (Art. I.2/I.5).
  > **RESOLVED (2026-07-03):** project decision — standardise on **F-SKU (F2+)** as the recommended/supported
  > capacity for this demo; P1+ remains **technically valid per the primary source** but is **out of scope**.
  > This is a scoping recommendation, **not a capability claim** (we do not assert P1+ is unsupported).
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

**Status: `Verified-Preview` — empirically Accessible on our subscription (2026-07-03).** The preview docs still
describe a sign-up / allow-list gate, but it was **not enforced** for us on this date.

The optimizer is real, documented, and in **limited public preview**. The preview pages still carry gate language
— the Quickstart prerequisites say *"Your Azure subscription must be on the allow list for the agent optimizer.
Contact your Microsoft representative to request access."*, and the shipped optimization sample README describes a
*"limited preview … intake form https://aka.ms/ao/preview-form"*. **However, in a validation spike on 2026-07-03
this gate was not enforced on our subscription:** `azd ai agent optimize` submitted a real job
(`Job ID: opt_2506b71b1a834c57b58c4060584310ea`, Status `queued` → `in_progress`) with **no 403 / allow-list
rejection** (job then cancelled for cost control). *(Empirical test evidence dated 2026-07-03 — our own observation,
not a Microsoft doc; see the evidence note below.)* We report **both** the doc gate language and the empirical
result: the native path is viable for us today, but we do **not** claim it is ungated for everyone.

**Primary sources (accessed 2026-07-03):**
- Overview — https://learn.microsoft.com/en-us/azure/foundry/agents/concepts/agent-optimizer-overview *(`ms.date` 2026-05-18, updated 2026-06-24)*
- Quickstart "Optimize a hosted agent" — https://learn.microsoft.com/en-us/azure/foundry/agents/quickstarts/quickstart-optimize-hosted-agent *(`ms.date` 2026-06-22, updated 2026-06-30)*
- Optimize targets — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/optimize-agent-targets
- Create dataset/evaluators — https://learn.microsoft.com/en-us/azure/foundry/agents/how-to/create-optimizer-dataset
- azd agent extension — https://learn.microsoft.com/en-us/azure/developer/azure-developer-cli/extensions/azure-ai-foundry-extension *(ms.date 2025-12-11)*

**Empirical evidence (validation spike, 2026-07-03 — our own test, not a Microsoft doc):** on our Foundry project
(East US 2) `azd ai agent optimize` was **accepted and processed** by the service — job `opt_2506b71b1a834c57b58c4060584310ea`
reached `in_progress` before being cancelled for cost — and `azd ai agent eval generate` ran end-to-end. This proves
**submission → queue → execution-start**; because the job was cancelled early, **final candidate scoring was not
observed** (that will be exercised in Phase 6). No scores are asserted here.

### 3a. Real extension & commands — Verified (tooling refreshed 2026-07-03)
- **Extension: `microsoft.foundry`** (the Foundry meta-extension), installed with
  **`azd ext install microsoft.foundry`** (upgrade with `azd ext upgrade microsoft.foundry`). It bundles the
  `azure.ai.agents` dependency (Quickstart requires **0.1.40-preview or later**; the spike observed
  `microsoft.foundry` **1.0.0-beta.1** bundling `azure.ai.agents` **1.0.0-beta.2**). Requires a **recent azd**
  (**≥ ~1.26**) and **Azure CLI** (`az login` + `azd auth login`). *(Empirical: azd **1.23.7 was rejected** with
  "no compatible version"; **1.27.0 worked** — 2026-07-03.)* The earlier "`azure.ai.agents` / azd 1.21.3+" note is
  **stale** — see Corrections.
- **Commands (verified):**
  - `azd ai agent init -m <agent-definition-or-manifest-url> [.] [-p <project-resource-id>]` — scaffold; generates
    `agent.yaml`, `.agent_configs/baseline/`, dataset, and IaC (`infra/`, `azure.yaml`).
  - `azd provision` → `azd deploy` (or `azd up`) → `azd ai agent invoke "<prompt>"` — provision/deploy/smoke-test.
  - `azd ai agent eval generate [--gen-instruction-file <f>] [--eval-model <m>] [--max-samples N]` — generate a
    domain-tuned `eval.yaml`, dataset, and evaluators. (`azd ai agent eval run` runs the eval suite.) *(The current
    Quickstart uses `eval generate`; an earlier note said `eval init` — see Corrections.)*
  - `azd ai agent optimize [--config eval.yaml] [--agent <name>] --eval-model <m> --optimize-model <m>`
    `[--max-candidates N] [--evaluator <name> ...] [-p/--project-endpoint <ep>] [--watch]` — auto-detects `eval.yaml`;
    runs the closed-loop optimization (~5–20 min). **Both `--eval-model` and `--optimize-model` are required** (the
    optimize-model may instead be set as `optimization_model` under `options:` in `eval.yaml`); `--max-candidates`
    **defaults to 5**; `--evaluator` is repeatable and required if evaluators aren't already in the config.
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
| **Model selection** | `options.optimization_config.model_search_space` list in `eval.yaml` | Scores the agent across multiple model deployments for quality/cost trade-off |

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
    model_search_space:          # presence enables the model-selection target
      - gpt-4.1
      - gpt-4.1-mini
      - gpt-4o
```
- **Two models:** `eval_model` (`--eval-model`) scores each task/criterion (binary 0/1 for `builtin.task_adherence`);
  `optimization_model` (`--optimize-model`) generates candidates and is **required** (missing → API error).
- **Supported `optimization_model` values:** must be from the **gpt-5 family or DeepSeek**. The Overview `#models`
  table (accessed 2026-07-03) lists **`gpt-5`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4`, `gpt-5.5`, `DeepSeek-V4-Pro`,
  `DeepSeek-V-3.2`**. *(Empirical: **`gpt-5.4` was accepted** by the service in our 2026-07-03 spike.)* The earlier
  narrower list (`gpt-5`/`gpt-5.1`/`gpt-5.3`) is superseded — see Corrections; any `eval_model` may be any deployed
  chat-completion model.
- **Dataset:** default built-in = **3 general coding tasks + 25 criteria**; custom datasets are **JSONL**, one
  task per line: `{"name","prompt","criteria":[{"name","instruction"}], "groundTruth"?}`.
- **Score interpretation (verified):** <0.03 noise · 0.03–0.10 moderate (worth deploying) · 0.10–0.20 significant ·
  >0.20 major.
- ⚠️ **Every dataset task invokes the agent**, executing any real tool calls — use test endpoints/mocks to avoid
  charges/state mutation (relevant to **Art. V** synthetic-fixtures discipline). If the eval model isn't deployed,
  **all scores silently return 0**.

### 3d. Known beta defects (observed 2026-07-03) — empirical test evidence
Two tooling defects were hit during the validation spike. Both are **observed in this beta build** (`microsoft.foundry`
1.0.0-beta.1 / `azure.ai.agents` 1.0.0-beta.2) and may change; neither is documented as a limitation on the primary
pages, so they are recorded here as our own observations, not doc-sourced claims.
- **(a) Brownfield `azd provision` with a declared model deployment fails `InvalidTemplate`** (malformed project
  resource name in the generated IaC). **Workaround:** don't declare the model deployment in the template / reuse an
  existing deployment.
- **(b) `azd ai agent optimize --no-prompt` cannot resolve the baseline instruction from config** — it errors
  "instruction is required" even when the instruction is set. It **works interactively only**, which blocks
  non-interactive / CI optimize runs today. *(Cf. the Quickstart troubleshooting row for `optimization_model is
  required` in non-interactive mode — a related, separate non-interactive gap.)*

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

**Role in this project:** the **conceptual anchor** for "text-space, non-parametric optimization" and a documented
**fallback custom loop** should the native Agent Optimizer path (§3) be unavailable. As of the 2026-07-03 spike the
native optimizer is **empirically accessible on our subscription**, so SkillOpt is now a **fallback, not a
necessity**. It targets the same text-space artifacts (`instructions.md`, skills, tool descriptions). Attribute
correctly to Microsoft Research (**Art. VII.2**).

---

## Corrections to the source PDF
Per **Art. I.5**, inaccuracies in the Gemini-generated source are corrected here:

1. **`fabric_iq_connection` tool type — inaccurate.** No such single tool. The real Foundry tool type is
   **`fabric_iq_preview`** (`FabricIQPreviewTool`).
2. **"MCP vs native connector" — false dichotomy; resolved as both.** The flagship native tool (`fabric_iq_preview`)
   is itself **built on MCP** (its `server_url` is a Fabric IQ MCP endpoint). There is also a portal **Foundry IQ
   knowledge base** path and a **raw ontology MCP endpoint** for any MCP client.
3. **azd extension name — corrected, then evolved.** *(Phase 0)* the extension was `azure.ai.agents`, **not**
   `microsoft.foundry`. **Update (2026-07-03):** the tooling has since changed — the Agent Optimizer is now installed
   via the **`microsoft.foundry`** meta-extension (`azd ext install microsoft.foundry`), which **bundles** the
   `azure.ai.agents` dependency. So the PDF's `microsoft.foundry` name is now the correct install target, though for a
   different reason than it originally implied. See §3a.
4. **Optimizer eval command — corrected, then reversed.** *(Phase 0)* dataset generation was recorded as
   `azd ai agent eval init`. **Update (2026-07-03):** the current Quickstart (updated 2026-06-30) and our spike both
   use **`azd ai agent eval generate`** — this reverses the Phase 0 correction. The verified command is now
   `eval generate`. See §3a.
5. **Model-selection YAML key — corrected, then reversed.** *(Phase 0)* the key was recorded as
   `options.optimization_config.model` (not `model_search_space`). **Update (2026-07-03):** the current Overview page
   shows the model-selection candidate list under **`options.optimization_config.model_search_space`** — this reverses
   the Phase 0 correction. The verified key is now `model_search_space`. See §3b/§3c.
6. **Supported optimization models — updated.** *(Phase 0)* primary docs listed `gpt-5`, `gpt-5.1`, `gpt-5.3`.
   **Update (2026-07-03):** the Overview `#models` table now lists **`gpt-5`, `gpt-5.1`, `gpt-5.2`, `gpt-5.4`,
   `gpt-5.5`, `DeepSeek-V4-Pro`, `DeepSeek-V-3.2`** (gpt-5 family **or** DeepSeek); `gpt-5.3` is no longer listed and
   `gpt-5.4` **was empirically accepted** by the service in our spike. Any deployed chat model may serve as
   `eval_model`. See §3c.
7. **Entra `Item.Execute.All` / `Item.Read.All` scopes — unverified.** Documented access is **delegated user
   identity** + a **BYO Entra app via managed OAuth**, with RBAC **Foundry User** + **Foundry Project Manager**
   (see §1c/§2a). Do not publish those scope strings as fact until confirmed in the app-registration flow.
8. **Optimizer availability — clarified, then re-tested.** *(Phase 0)* it was described as a **limited preview gated
   by a subscription allow-list** ("contact your Microsoft representative"; 403 otherwise). **Update (2026-07-03):**
   the docs **still carry** allow-list / intake-form language, but the gate was **empirically not enforced** on our
   subscription — `azd ai agent optimize` submitted a real job (no 403). We report both; see §3 header.

## Gaps, risks & fallbacks (summary)
| # | Gap / risk | Impact | Fallback |
| --- | --- | --- | --- |
| G1 | **Agent Optimizer preview gating** (§3) — **RESOLVED-BY-TEST** | Native optimization demo | **Empirically accessible on our subscription (2026-07-03):** `azd ai agent optimize` submitted a real job with no 403. Preview sign-up / allow-list language persists in the docs but was **not enforced** for us. Native path viable; **SkillOpt (§4) is now a fallback, not a necessity**. (Two beta tooling defects noted in §3d; final candidate scoring to be exercised in Phase 6.) |
| G2 | **Service-principal Entra scopes for Fabric IQ undocumented** (§1c) | Automation/CI (non-interactive) auth uncertain | Use **delegated user identity** as documented; re-verify SP scopes before publication |
| G3 | Ontology **binding limitations** (managed tables, no OneLake security, no column mapping) | Constrains fixture design | Design Phase 3 synthetic fixtures to comply from the start |
| G4 | Graph feature needs **tenant Graph setting**; upstream data needs **manual refresh** | Setup/latency friction | Document as prerequisites; script the refresh in the repo |
| G5 | Fabric IQ preview may **incur cost / send data outside the Azure compliance boundary** (§2a) | Compliance (Art. VI/VII) | Gate real-data wiring behind explicit approval; keep synthetic fixtures for the public demo |

## Gate decision
Phase 0's verification objective is met: every load-bearing claim now carries a primary-source citation and a
stated status. All four capabilities are real. The Phase 0 hard dependency — Agent Optimizer allow-list access (G1)
— has been **resolved by test (2026-07-03):** the optimizer is **empirically accessible on our subscription** (a real
`optimize` job was submitted with no 403), so the **fully-native optimization path is viable** and SkillOpt (§4)
remains a documented fallback rather than a necessity. **Recommendation to the master session:** (a) proceed with the
native optimizer for Phases 6–7 while keeping the SkillOpt-style path as a drop-in fallback; (b) account for the two
beta tooling defects in §3d (brownfield `azd provision` template failure; non-interactive `optimize` instruction-
resolution defect — run `optimize` interactively for now); and (c) exercise end-to-end candidate scoring in Phase 6
(the spike proved submission/queue/execution-start but cancelled before scoring). Per **Art. XIII**, no Phase 1+
build work should begin until this note is merged.
