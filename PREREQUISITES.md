# Prerequisites

> **Issue:** #15 (EPIC A, #1) · **Phase:** 2 (repo scaffold, prerequisites & governance)
> **Governs:** Constitution Art. I (Accuracy & Verification), Art. VI (Security & Secrets).
>
> Every technical claim below is sourced from [`docs/verified-capabilities.md`](./docs/verified-capabilities.md)
> — the single source of truth for this initiative — which in turn cites primary Microsoft sources
> (verification date **2026-07-03**). Preview/GA status is stated per item. Where a value could not be
> confirmed against a primary source it is flagged **Unverified** with its tracking issue.

This is an **infra-free** phase: nothing here needs to be provisioned to scaffold the repo. This document
lists what will be required to *run* the demo in later phases (3–7). Do **not** run `azd`, Azure CLI, or
any Fabric/Foundry provisioning as part of Phase 2.

---

## 1. Microsoft Fabric — capacity, workspace & tenant settings

**Status:** `Verified-Preview` (Fabric IQ / ontology is in public preview).
**Source:** `docs/verified-capabilities.md` §1, §1c.

- **Capacity — a paid `F2` or higher Fabric capacity (F-SKU).**
  This is the recommended, unambiguous target for the demo. The ontology (preview) item is part of the
  **Fabric IQ (preview) workload**; a paid **F2+** capacity is the baseline we standardise on.
  - **On the P1+/Premium question (important):** the current primary source (**Use Ontology MCP Server**,
    Microsoft Learn, `updated_at` 2026-06-30) *also* lists **Power BI Premium per-capacity `P1` or higher
    with Microsoft Fabric enabled** as technically valid, and the **Features by SKU and Capacity**
    feature-parity list does not carve ontology out as F-SKU-only. **Resolution (2026-07-03):** this demo
    standardises on **F-SKU (F2+)**. P1+ remains **technically valid per the primary source** but is
    **out of scope** for this project — **F-SKU only** (see `docs/verified-capabilities.md` §1c re-verification
    note). This is a deliberate scoping recommendation for clarity and consistency, **not** a claim that P1+
    is unsupported.
  - Trial capacities are **not** assumed to support these preview features.
- **Workspace** assigned to that F2+ capacity, in which the ontology (preview) item and its bound OneLake
  sources (Lakehouse / Eventhouse / Power BI semantic model) will live.
- **Tenant settings (Fabric admin portal → tenant settings):**
  - **`Enable Ontology item (preview)`** — **required** to create ontology items (errors on creation
    otherwise). *(verified-capabilities.md §1c; overview-tenant-settings)*
  - **`Graph in Microsoft Fabric`** — required for the graph feature / GQL traversal used by NL2Ontology.
    *(verified-capabilities.md §1a, §1c)*
  - Fabric **data agent** / **operations agent** tenant settings are required **only** if the ontology is
    consumed through those agents (not required for the `fabric_iq_preview` tool path we use).

**Binding constraints to design fixtures around (Phase 3/4):** Lakehouse tables must be **managed**, must
**not** have OneLake security enabled, and must **not** have column mapping enabled; upstream row changes
require a **manual graph refresh**. *(verified-capabilities.md §1a; risk G3/G4)*

---

## 2. Azure AI Foundry — project & model deployment

**Status:** `Verified-Preview` (Fabric IQ grounding is preview; hosted agents are a Foundry Agent Service capability).
**Source:** `docs/verified-capabilities.md` §2, §1c.

- An existing **Foundry project/instance**.
- **At least one model deployment** (a **GPT-5 family** chat-completion deployment — the demo baseline in the
  plan is GPT-5.4). A hosted agent references a **model *deployment* by name** (a config string), so the model
  stays a swappable commodity (Art. III) and weights stay frozen (Art. II). *(verified-capabilities.md §2b)*
- **Azure RBAC (for the `fabric_iq_preview` tool):**
  - **Foundry User** on the project — for the developer identity, the agent runtime identity, and any user
    identity used in OAuth flows.
  - **Foundry Project Manager** — to create the Fabric IQ connection.
  - Invoking users also need a **Microsoft Fabric license** with access to the queried items.
  *(verified-capabilities.md §1c; tools/fabric-iq)*

---

## 3. Identity & authentication

**Status:** `Verified-Preview` for delegated identity · **`Unverified`** for service-principal scopes (#11).
**Source:** `docs/verified-capabilities.md` §1c, §2a; Corrections #7; risk G2.

- **Delegated user identity (verified path).** Access is identity-based / user-identity passthrough: the
  `fabric_iq_preview` tool runs **all requests in the context of the signed-in user**, honouring Fabric
  permissions/governance. The signed-in identity must have access to **both** the Fabric workspace **and**
  the Foundry project. This is the path the demo uses.
- **BYO Entra app + managed OAuth.** A bring-your-own **Microsoft Entra app registration** provides managed
  OAuth (Foundry API token scope `https://ai.azure.com/.default`).
- **⚠️ Service-principal scopes are `Unverified` (tracked in #11).** The source PDF's specific
  `Item.Execute.All` / `Item.Read.All` Entra app-registration scopes are **not corroborated** by the primary
  preview docs. **Do not treat any SP scope list as fact.** **Fallback:** proceed with delegated user
  identity as documented; re-confirm SP scopes against the BYO Entra-app registration flow / Fabric REST API
  docs before they enter the public article. *(verified-capabilities.md Corrections #7; risk G2)*

---

## 4. Local tooling

**Status:** `Verified` (versions/extension confirmed) · Python runtime **settled in Phase 3**.
**Source:** `docs/verified-capabilities.md` §3a; Phase 3 (issue #20).

- **Azure Developer CLI (`azd`) `1.21.3+`.**
- **`azure.ai.agents` azd extension** — installed with `azd ext install azure.ai.agents` (equivalently
  `azd extension install azure.ai.agents`; auto-installs on first `azd ai agent ...` use).
- **Azure CLI** — for `az login` (paired with `azd auth login`).
- **Python `3.10+`** (settled in Phase 3). The Phase 3/4 data + ontology scripts under `scripts/` depend on:
  **pandas** (`>=2.0`), **pyarrow** (`>=14.0`), **deltalake** / delta-rs (`>=0.17`), **azure-identity**
  (`>=1.15`), **requests** (`>=2.31`), **python-dotenv** (`>=1.0`) — pinned in
  [`requirements.txt`](./requirements.txt) (`pip install -r requirements.txt`). Pins align with the
  `ajananth/water-quality-assistant` data-seeder reference.
- **git** and the **GitHub CLI (`gh`)** — for the Epic → Issue → PR workflow (Art. XIII).

> Note: `azd`, Azure CLI, and Fabric/Foundry provisioning are **not** exercised in Phase 2 or Phase 3
> (authoring only). The `scripts/` load + ontology deploy run in **Phase 4**.

---

## 5. Agent Optimizer access (gated)

**Status:** `Gated` — limited public preview behind a **subscription allow-list** (#10).
**Source:** `docs/verified-capabilities.md` §3; risk G1.

- The **Foundry Agent Optimizer** (`azd ai agent optimize`, via the `azure.ai.agents` extension) requires the
  Azure **subscription to be on the allow-list** — *"Contact your Microsoft representative to request access."*
  A gated `optimize` call returns **403**.
- **This is the single biggest dependency risk (G1).** Request allow-list access early (tracked in **#10**).
- **Fallback — SkillOpt.** If allow-list access is not granted, use a **SkillOpt-style custom loop**
  (Microsoft Research; MIT; PyPI `skillopt`; Python 3.10+) targeting the same text-space artifacts
  (`instructions.md`, skills, tool descriptions) to demonstrate the identical non-parametric loop.
  *(verified-capabilities.md §4)*

---

## 6. Cost & compliance note

**Status:** preview cost caveat (verified from the primary source page).
**Source:** `docs/verified-capabilities.md` §2a; risk G5.

- **Fabric IQ preview may incur cost**, and the Foundry page warns that connecting to Fabric IQ may send data
  outside the Azure compliance boundary. For this project the **G5 data-boundary concern is largely moot —
  all demo data is synthetic** (Art. V) — but the **cost note stands**: provisioning F2+ capacity and running
  preview features will accrue charges. Every dataset task in the optimizer also **invokes the agent**
  (executing real tool calls), so use synthetic fixtures / test endpoints to avoid charges and state mutation.

---

## Summary checklist

| # | Prerequisite | Status | Source (verified-capabilities.md) |
| --- | --- | --- | --- |
| 1 | Paid **F2+** Fabric capacity (F-SKU only; P1+ out of scope) | `Verified-Preview` | §1, §1c |
| 2 | Fabric **workspace** on that capacity | `Verified-Preview` | §1c |
| 3 | Tenant settings: **Enable Ontology item (preview)** + **Graph in Microsoft Fabric** | `Verified-Preview` | §1c |
| 4 | Foundry **project** + ≥1 **GPT-5-family model deployment** | `Verified-Preview` | §2 |
| 5 | RBAC: **Foundry User** + **Foundry Project Manager** (+ Fabric license) | `Verified-Preview` | §1c |
| 6 | **Delegated user identity** with access to both workspace + project | `Verified-Preview` | §1c |
| 7 | **BYO Entra app** + managed OAuth (SP scopes **Unverified**, #11) | `Unverified` (SP scopes) | §1c, Corrections #7 |
| 8 | **azd 1.21.3+**, **`azure.ai.agents`** ext, **Azure CLI**, **Python 3.10+** (+ pandas/pyarrow/deltalake/azure-identity/requests/python-dotenv, see `requirements.txt`) | `Verified` | §3a |
| 9 | Agent Optimizer **allow-list** (#10) — else **SkillOpt** fallback | `Gated` | §3, §4 |
| 10 | Awareness: **Fabric IQ preview cost** | preview caveat | §2a |
