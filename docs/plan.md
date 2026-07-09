# Plan: Non-Parametric Learning on the Microsoft IQ Stack (Public Article + Repo)

## Problem / Goal
Produce a **public article backed by a runnable, deployable GitHub repo** demonstrating how to
combine the **Microsoft IQ stack** (Fabric IQ Ontology + Foundry IQ / Foundry Agent Service) for
enterprise *context* with **non-parametric learning** (frozen model weights; optimize the harness,
prompts, tools, and skills) to:

1. Optimize the agent harness without touching model weights (fast, auditable, no catastrophic forgetting).
2. Demonstrate **frontier model swappability / model independence** (the headline value).
3. Demonstrate the **Fabric IQ ↔ Foundry semantic contract** (the other headline value).

**Domain scenario:** Water utilities — monitoring & responding to **algal blooms** (cyanobacteria,
MIB/Geosmin taste-and-odor compounds, cyanotoxins) across four related **Lakehouse tables**: monitored
**Sites**, an **AlgaeSpecies** catalogue, time-series **WaterQualityMeasurements**, and **TreatmentRecords**.

## Ways of working (governed by the Constitution)
- All work lives in a **dedicated workspace/session**: `iq-nonparametric-learning`
  (`C:\Users\ajananth\Projects\iq-nonparametric-learning`), not scattered across chats.
- **Master / child orchestration:** one **master (orchestrator) session** owns the plan + constitution
  and delegates workstreams to **child sessions** (as done for Research IQ). Every child session must
  comply with the constitution before acting.
- **Plan-before-implement (hard gate):** every activity is thoroughly planned; **no implementation
  starts in any session until the user has approved that plan.**
- **GitHub traceability (hard gate):** no change — however small — is executed unless backed by a
  high-level **Epic → Issue → PR** chain. This is verified before every task in every session. Merges
  only via reviewed PRs; no direct pushes to the default branch.
- A GitHub repo is created **private** to host epics/issues/PRs, and made **public only at the
  publication approval gate**.
- **`CONSTITUTION.md`** is the governing document — hard rules that always apply (accuracy/verification,
  non-parametric integrity, model independence, separation of concerns, reproducibility, secrets
  hygiene, public-content safety, human approval gates, plan traceability, orchestration, GitHub
  traceability).
- Read the Constitution at the start of each major phase; amend only with user consent (dated).
- `plan.md` + the todo DB are the single source of truth; small, auditable increments.
- Explicit approval gates: repo name, making repo public, first public push, article publication.

## Key decisions (confirmed with user)
- **Repo type:** Runnable end-to-end demo others can deploy.
- **Data:** User will provide **real water utility data** to wire in (repo ships synthetic fixtures so
  it is reproducible without that data; real data slots in via config).
- **Location:** New standalone **public repo** — name TBD (see naming shortlist below).
- **Optimizer:** Foundry **Agent Optimizer** (`azd ai agent optimize`) as the primary path; SkillOpt
  referenced as the research foundation / alternative custom-loop path.
- **Model:** Start with GPT-5.4; use `model_selection` search space to prove swappability
  (e.g. GPT-5.4 vs GPT-5.4 mini vs an open-weights model).

## Two headline narratives to foreground
1. **Fabric IQ = the "semantic contract."** Data structure & business vocabulary live in the ontology,
   not in prompts. Cross-domain reasoning (stream + lab + asset) via graph traversal; standardized
   MCP tooling; fails safely (structural alert vs silent hallucination).
2. **Model swappability = decoupled compute.** Because the ontology owns the schema, the model becomes
   a commodity you can swap (cost/accuracy) with zero code rewrites — flip an endpoint / config.

## ⚠️ Accuracy caveat
The source PDF is Gemini-generated and self-flagged as possibly inaccurate. Several specifics
(`fabric_iq_connection` tool type, exact `azd` flags, `model_search` YAML keys, Fabric IQ endpoint
shape, whether the Foundry↔Fabric IQ link is MCP vs a native connector) MUST be verified against live
Microsoft Learn docs before publishing. This is **Phase 0** and gates everything else.

---

## Phases & Todos

### Phase −1 — Establish workspace, constitution & governance (DONE)
- Dedicated project folder `iq-nonparametric-learning` created and context seeded. ✔
- `CONSTITUTION.md` authored (13 articles incl. orchestration, plan-before-implement, Epic→Issue→PR)
  and user-approved. ✔
- This designated the **master (orchestrator) session** ("IQ NPL — Master"). ✔
- Private GitHub repo created: **github.com/ajananth/iq-nonparametric-learning** (initial commit pushed). ✔
- Top-level **Epics** created (issues #1–#7):
  - #1 EPIC A — Governance & repo scaffolding (Phases −1, 2)
  - #2 EPIC B — Feasibility validation & article narrative (Phases 0, 1)
  - #3 EPIC C — Water-utility semantic layer in Fabric IQ (Phases 3, 4)
  - #4 EPIC D — Foundry agent harness (Phase 5)
  - #5 EPIC E — Non-parametric optimization loop (Phase 6)
  - #6 EPIC F — Model swappability experiment (Phase 7)
  - #7 EPIC G — Article write-up & publication (Phase 8)

> **Governance rule for every phase below:** each todo is delivered as **Issue → PR** under its phase
> **Epic**, planned and user-approved before implementation, per Articles XI–XIII.

### Phase 0 — Validate feasibility against live docs (GATE) — DONE ✅
Delivered as `docs/verified-capabilities.md` (dated 2026-07-03) via PR #9 (merged), issue #8.
- **Fabric IQ Ontology (preview)** — Verified-Preview. Entity/relationship/property authoring + OneLake
  data binding (Lakehouse/Eventhouse/PBI); NL2Ontology (GQL/KQL). Binding limits noted.
- **Foundry Agent Service grounding** — Verified-Preview. Native **`fabric_iq_preview`** tool
  (`FabricIQPreviewTool`, azure-ai-projects≥2.2.0) **built on MCP** (server_url = Fabric IQ MCP endpoint);
  portal Foundry IQ knowledge-base path also exists. Frozen weights by construction.
- **Foundry Agent Optimizer** — **Gated** (real + preview, but subscription **allow-list** required; 403
  otherwise). Verified commands/targets/eval.yaml schema; optimizer models = gpt-5/5.1/5.3. → Action #10.
- **SkillOpt** — Verified-GA (repo + arXiv:2605.23904 + PyPI). Conceptual anchor + fallback loop.
- **Key resolution:** "MCP vs native connector" was a false dichotomy — native tool is built on MCP.
- **PDF corrections** recorded (tool type, azd extension, eval cmd, model-select key, model list, Entra scopes).
- **Follow-ups:** #10 (G1 optimizer allow-list — hard dep), #11 (G2 SP Entra scopes), #12 (G5 real-data compliance gate).
- **Carry-forward:** design Phase 6 (EPIC E) so the SkillOpt-style custom loop is a drop-in if #10 is delayed.

### Phase 1 — Article outline & narrative spine (NEXT)
- Draft article structure (problem → IQ stack → non-parametric concept → water scenario → build →
  optimization results → swappability results → takeaways).
- Nail the demo hook / thesis (separation of concerns: Fabric IQ owns truth, Foundry swaps the brain).
- Decide publish target (dev.to / Microsoft community / personal blog) and license (MIT for code,
  CC-BY for prose).

### Phase 1 — Article outline & narrative spine — DONE ✅
Delivered as `docs/article-outline.md` via PR #14 (merged), issue #13. EPIC B (#2) complete.
- Working title (final title, merged in #35): *Optimize the Harness — Non-Parametric Learning on the Microsoft IQ Stack*.
- Thesis/hook, target audience, 10-section outline, two dedicated headline-narrative sections, a C1–C9
  accuracy register tied to verified-capabilities.md, and honest gate/placeholder flags.
- Publication recommendation: **Microsoft Tech Community** (primary) + **dev.to** cross-post (canonical
  back); personal blog fallback. Licenses: code MIT, prose CC-BY. (Publication is an Art. VIII gate.)

---

## ⏸️ CURRENT STATE — APPROVAL / DEPENDENCY GATE (as of 2026-07-03)
Phases −1, 0, 1 complete (all planning/validation/authoring — delivered via reviewed PRs, repo private).
**All remaining phases (2–8) are build/implementation work.** Per **Constitution Art. XII**, implementation
requires explicit user plan approval; several phases also have **external dependencies only the user can
resolve**:
- **#10 (G1)** Foundry Agent Optimizer allow-list — hard dep for Phases 6–7 (native path); SkillOpt fallback designed in.
- Azure/Fabric infra the master session cannot provision autonomously: **Fabric F2+ capacity**, tenant
  settings (Enable Ontology item; Graph), a **Foundry project**, and **Entra** app/identity (Phases 4–7).
- **#12 (G5)** real-data wiring gated behind compliance review; public demo uses synthetic fixtures.

**Recommended next step for the user:** approve the **Phase 2 (repo scaffold)** plan — it is low-risk,
infra-free build work (directory skeleton, templates, `.env.example`, issue/PR templates) that can proceed
while the optimizer allow-list request (#10) and Azure/Fabric provisioning happen in parallel.

### Phase 2 — Repo scaffold & naming
- Repo name confirmed: **`iq-nonparametric-learning`** (private). Create public repo scaffold: README,
  LICENSE, docs/, infra/, ontology/, agent/ (.agent_configs/baseline: instructions.md, tools.json),
  eval/ (eval.yaml + datasets), data/ (synthetic fixtures + real-data slot), scripts/.

### Phase 3 — Domain & data model (water utility / algal bloom)
- Define ontology (over the real synthetic dataset; CSV headers authoritative): entities **Site**,
  **AlgaeSpecies**, **WaterQualityMeasurement**, **TreatmentRecord** (properties = real CSV columns,
  key = each `*_id`); relationships **hasMeasurement** (Site→WaterQualityMeasurement, `site_id`),
  **hasTreatment** (Site→TreatmentRecord, `site_id`), **dominantSpecies**
  (WaterQualityMeasurement→AlgaeSpecies, `dominant_species_id`).
- Vendor 4 synthetic CSVs; author ontology (updateDefinition parts) + scripts + docs. **Authoring only**
  — no live Fabric (that is Phase 4).

### Phase 4 — Fabric IQ ontology build
- **Flat** load (no medallion) of the 4 CSVs into 4 **managed** Lakehouse Delta tables
  (`scripts/load_lakehouse.py`), then deploy the ontology definition + bindings via **updateDefinition**
  (`scripts/deploy_ontology.py`), and validate NL2Ontology queries.

### Phase 5 — Foundry agent harness
- Entra app registration + permissions.
- Hosted agent config: instructions.md (persona), tools.json (Fabric IQ tool), model = GPT-5.4.
- Baseline invoke sanity test.

### Phase 6 — Non-parametric optimization loop
- eval.yaml: algal-bloom task dataset + criteria rubrics (multi-step ontology traversal, negative
  guardrails against task overexpansion, reasoning_effort calibration).
- Run optimizer; capture written logs, candidate ranking, text-diffs of instructions/tools.

### Phase 7 — Model swappability experiment
- Configure model_selection search space (GPT-5.4 / GPT-5.4 mini / open-weights).
- Run sweep; capture cost vs accuracy scorecard proving a smaller optimized model matches flagship.

### Phase 8 — Write-up, diagrams & polish
- Architecture diagrams (data → ontology → agent; model-swap fan-out).
- Reproduction guide, screenshots, results tables, "how to plug in your own data/ontology".
- Final editorial pass on the public article.

---

## Repo name (CONFIRMED)
- **`iq-nonparametric-learning`** — private for now; made public only at the publication approval gate.

## Open questions to resolve as we go
- Exact Fabric IQ ↔ Foundry connection mechanism (MCP tool vs native connector) — resolved in Phase 0.
- Which open-weights model to include in the swap pool.
- Whether real data can be shared publicly or only referenced via a config slot.
