# Article Outline — Non-Parametric Learning on the Microsoft IQ Stack

> **Issue:** #13 (EPIC B, #2) · **Phase:** 1 — Article outline & narrative spine
> **Status:** Draft outline for review (authoring/planning only — no build work)
> **Governs:** Constitution Art. I (Accuracy), Art. II (Non-Parametric Integrity), Art. III (Model
> Independence), Art. IV (Separation of Concerns), Art. VII (Public-Content Safety), Art. VIII &
> Art. XIII (approval gates / Issue→PR).
> **Source of truth for every technical claim:** [`docs/verified-capabilities.md`](./verified-capabilities.md)
> (Phase 0 gate, verified 2026-07-03). Nothing in the finished article may contradict that note; where a
> capability is `Gated` or `Unverified` there, the article must say so.

---

## 1. Working title + one-line thesis / demo hook

**Working title (lead candidate) — final title, merged in #35:**
> **"Optimize the Harness — Non-Parametric Learning on the Microsoft IQ Stack"**

**Alternate titles (for editorial choice):**
- "Your Enterprise Data Deserves a Semantic Contract — Not a Prompt: Fabric IQ + Foundry for a Water Utility"
- "Swap the Brain, Keep the Truth: Model-Independent Agents on Fabric IQ and Foundry"

**One-line thesis / demo hook:**
> **Fabric IQ owns the *truth* of the water network's data and semantics; Foundry lets you swap the model
> on top — so you upgrade to newer frontier models, or drop to a cheaper optimized one, *without rewriting
> your enterprise data architecture*. And you improve the agent by optimizing text (instructions, tools,
> skills), never by touching model weights.**

**Demo hook (the "show me" moment):** a water-utility agent answers a cross-domain algal-bloom question
that spans monitoring sites, water-quality measurements, algae-species toxicity, and treatment history —
then we (a) swap the underlying frontier model via *config only* and watch it still work, and (b) show an
*auditable text diff* of how the agent's instructions/tools were optimized, with the model weights provably
untouched.

---

## 2. Target audience & key takeaways

**Primary audience:** enterprise **data & AI architects** and platform/ML engineering leads evaluating how
to ground LLM agents in governed enterprise data on Microsoft Fabric + Azure AI Foundry.

**Secondary audience:** technical decision-makers weighing frontier-model lock-in / cost, and data
engineers who own the Fabric semantic layer.

**Key takeaways (the two headline values, foregrounded):**
1. **The Fabric IQ ↔ Foundry semantic contract.** Data structure and business vocabulary live in the
   **ontology**, not in prompts. The agent reasons across stream + lab + asset data via **graph traversal**
   over a typed ontology, and **fails safely** (a structural/authorization boundary rather than a silent
   hallucination). *(Art. IV; verified-capabilities §1, §2.)*
2. **Frontier model swappability / model independence.** Because the ontology owns the schema and
   semantics, the model is a **commodity behind config** — swap it with **no code rewrite**, and prove a
   smaller optimized model can approach a flagship on a **cost-vs-accuracy** scorecard. *(Art. III;
   verified-capabilities §2b, §3b model-selection target.)*

**Supporting takeaway:** *non-parametric* optimization (frozen weights; optimize the harness) is a real,
auditable engineering discipline — via the **Foundry Agent Optimizer** where access is granted, or a
**SkillOpt-style custom loop** where it is not.

---

## 3. Full section-by-section outline

> Ordering follows the issue spec: problem → the Microsoft IQ stack → non-parametric learning →
> water/algal-bloom scenario → building the Fabric IQ semantic layer → the Foundry agent harness → the
> non-parametric optimization loop → results (auditable diffs) → model swappability → takeaways/CTA.
> The two headline narratives (§4 below) are given their own dedicated sections (§S5.5 and §S9).

### S1. The problem — prompts are the wrong place for enterprise truth
- The failure mode: teams cram schema, business vocabulary, and join logic into prompts. Result: brittle,
  model-specific, un-auditable, and it *hallucinates confidently* when it can't answer.
- Two coupled costs: (a) **semantics coupled to prompts** and (b) **logic coupled to a specific model**.
- Thesis restated: separate the two — put truth in a **semantic layer**, treat the model as swappable, and
  optimize the agent in **text space** without retraining.
- **Claim-to-verify anchor:** framing only; no product claims here.

### S2. The Microsoft IQ stack — where enterprise context lives
- **Fabric IQ Ontology (preview):** the semantic layer over OneLake — entity types, typed/directional
  relationships with attributes and cardinality, properties, and **data bindings** to real OneLake data
  (Lakehouse tables, Eventhouse streams, Power BI semantic models) *without copying it*.
- **NL2Ontology** querying: business-term questions → structured queries dispatched to the most efficient
  engine (**GQL** for Graph in Fabric, **KQL** for Eventhouse).
- **Azure AI Foundry Agent Service:** hosts the agent (model deployment + instructions + tools) and grounds
  it in Fabric IQ via the **Foundry IQ Knowledge Base `/retrieve` + inject** path (the native
  `fabric_iq_preview` tool was disqualified 2026-07-08 — §2a/§2b).
- Explicitly state **preview status + date** and the tenant/capacity prerequisites at a high level.
- **Claims-to-verify:** ties to verified-capabilities **§1** (ontology), **§1b** (three grounding paths;
  we use the **KB retrieve+inject** path — §2b, adopted 2026-07-08), **§2a/§2b** (grounding wiring). Preview, verified 2026-07-03.

### S3. Non-parametric learning — optimize the harness, freeze the weights
- Define the term for this context: **the model's weights never change**; all optimization happens in
  **text space** — instructions, tool/parameter descriptions, skills, and *model selection*.
- Why it matters: fast, auditable, reversible, no catastrophic forgetting, and it keeps the model swappable.
- Preview the two engines we use: **Foundry Agent Optimizer** (native) and **SkillOpt** (research anchor /
  fallback). Name the honest caveat early: the optimizer is **allow-list gated**.
- **Claims-to-verify:** verified-capabilities **§2b** (frozen by construction), **§3** (optimizer targets),
  **§4** (SkillOpt). Art. II is the governing rule.

### S4. The scenario — a water utility responding to an algal bloom
- Why water utilities: high-stakes, genuinely cross-domain, and relatable. **Algal blooms** (cyanobacteria)
  produce **taste-and-odor** compounds and **cyanotoxins**; response requires fusing monitoring, species
  knowledge, and past interventions across the network.
- The demo grounds on a **real synthetic dataset** (Southeast Queensland water utility) of **4 flat tables**
  — one **managed Delta table** each, **no medallion** (issue #20; `data/README.md`):
  - **`sites`** — monitored water bodies (reservoir / wetland / coastal bay-lagoon) with location + status.
  - **`algae_species`** — species with `toxicity_level` and `bloom_trigger_conditions`.
  - **`water_quality_measurements`** — timestamped readings (`ph`, `dissolved_oxygen_mgl`, `turbidity_ntu`,
    `chlorophyll_a_ugl`, `nitrate_mgl`, `phosphate_mgl`, `algae_cell_count_cells_ml`) linked to a site and a
    dominant species.
  - **`treatment_records`** — remediation actions (`method`, `dosage_or_description`, `outcome`) per site.
- The question the agent must answer spans sites, measurements, species toxicity, and treatment history at
  once — the natural fit for graph traversal over the ontology's typed relationships.
- **Reproducibility note (Art. V):** the public demo ships **synthetic fixtures** (`data/`, derived from
  `ajananth/water-quality-assistant`); real utility data wires in via config only and is never committed.
  Fixtures are designed to respect ontology **binding limits** (managed tables; no OneLake security; no column
  mapping). *(verified-capabilities §1a, G3.)*

### S5. Building the semantic layer in Fabric IQ
- Model the domain as an ontology: entities (**Site, AlgaeSpecies, WaterQualityMeasurement,
  TreatmentRecord**), relationships (**hasMeasurement / hasTreatment / dominantSpecies**), properties = the
  real CSV columns (pH, dissolved oxygen, turbidity, chlorophyll-a, nitrate, phosphate, algae cell count,
  toxicity level, bloom triggers, treatment method/outcome). *(see `ontology/README.md`.)*
- Bind entities to **managed Lakehouse Delta tables** (`sites`, `algae_species`,
  `water_quality_measurements`, `treatment_records`); map columns→properties, define entity keys (each
  `*_id`), and map foreign keys→relationships. *(Eventhouse streams and Power BI semantic models are also
  valid binding sources per §1a, but this synthetic demo uses flat Lakehouse tables — no medallion.)*
- Prerequisites stated honestly: **F2+ capacity** (or P1+ with Fabric), **Enable Ontology item (preview)**
  tenant setting, and **Graph in Microsoft Fabric** enabled for graph traversal; upstream row changes need
  a **manual graph refresh**. *(verified-capabilities §1a, §1c, G4.)*
- **Claims-to-verify:** verified-capabilities **§1** end-to-end; call out binding limitations as design
  constraints, not incidental footnotes.

#### S5.5 — HEADLINE #1: The Fabric IQ ↔ Foundry semantic contract *(dedicated — see §4a)*

### S6. The Foundry agent harness
- Define the Foundry agent: **model deployment (by name) + `instructions.md` + tools** — grounded via the
  Fabric IQ **Knowledge Base `/retrieve` + inject** path (the harness POSTs `/knowledgebases/{kb}/retrieve`
  and injects verbatim ontology rows; `azure-ai-projects >= 2.2.0` for the Foundry agent client). *(§2b.)*
- Auth model stated accurately: **delegated user identity** (requests run in the signed-in user's context,
  honoring Fabric permissions) + BYO Entra app via managed OAuth; RBAC **Foundry User** + **Foundry Project
  Manager**. *(verified-capabilities §1c, §2a.)*
- The harness is **model-agnostic**: the model is referenced as a *config string*, not baked into code.
- Baseline sanity invoke before any optimization.
- **Claims-to-verify:** verified-capabilities **§2a/§2b**. **Honest gap:** specific service-principal Entra
  scopes (`Item.Execute.All` etc.) are **Unverified** — the article uses delegated identity as documented
  and flags SP scopes as not-yet-confirmed. *(verified-capabilities Corrections #7, G2.)*

### S7. The non-parametric optimization loop
- What gets optimized (the four targets, all text/config): **instruction tuning** (`instructions.md`),
  **skill improvement** (`skills/`), **tool optimization** (tool/parameter *descriptions* only), and
  **model selection** (`options.optimization_config.model` list). *(verified-capabilities §3b.)*
- The loop: evaluate baseline → generate candidates (reflection/`optimization_model`) → evaluate
  (`eval_model`) → rank by composite score (0.0–1.0) → deploy the winner. Nothing updates weights.
- Show a real, corrected **`eval.yaml`** shape and a JSONL task/criteria example; note score-interpretation
  bands and the "every task invokes the agent → use mocks/test endpoints" cost warning.
- **THE HONEST GATE (must be prominent):** the Foundry **Agent Optimizer is allow-list gated** — a
  non-allow-listed subscription gets **403**. State this plainly and present the **SkillOpt-style custom
  loop** as the drop-in fallback that optimizes the same text-space artifacts, with no weight updates.
  *(verified-capabilities §3, §4, G1; follow-up issue #10.)*
- **Claims-to-verify:** verified-capabilities **§3a–§3c** (commands, targets, eval.yaml, supported
  `optimization_model` = **gpt-5 / gpt-5.1 / gpt-5.3** — do not publish a wider list), **§4** (SkillOpt).

### S8. Results — auditable diffs
- The auditability story: optimization produces **text diffs** of `instructions.md` / tool descriptions /
  skills plus a candidate ranking with scores — reviewable in a PR like any code change.
- Present the *shape* of results (before/after instruction excerpts; score deltas with the verified
  interpretation bands) rather than fabricated numbers; final numbers are produced in Phases 6–7.
- Emphasize **provably frozen weights**: nowhere in the loop is there a fine-tune/weight-update step.
- **Claims-to-verify:** verified-capabilities **§3a** (score bands), **§2b/§3** (no weight update). Any
  concrete metric published later must come from an actual run (Art. I) — placeholder-flagged in the draft.

#### S9 — HEADLINE #2: Frontier model swappability / model independence *(dedicated — see §4b)*

### S10. Takeaways & call to action
- Recap the two headline values and the non-parametric discipline.
- Practical checklist: put semantics in the ontology; keep the model in config; optimize text, not weights;
  audit changes via diffs; plan for the optimizer gate with a fallback.
- **CTA:** clone the repo, run it on synthetic fixtures, wire your own ontology/data via config. Links to
  the (private-until-approved) repo and to `docs/verified-capabilities.md`.
- **Gate reminder (Art. VIII):** the repo/article go public only at the explicit publication approval gate.

---

## 4. Dedicated sections for the two headline narratives

### 4a. HEADLINE #1 — The Fabric IQ ↔ Foundry semantic contract (article §S5.5)
- **Claim:** data structure + business vocabulary live in the **ontology**, not in prompts; the agent
  queries semantics via NL2Ontology / the Fabric IQ **KB retrieve+inject** path, with **no raw SQL/schema coupling** in
  the harness. *(Art. IV; verified-capabilities §1, §1b, §2b.)*
- **Cross-domain graph traversal:** one question joins sites, measurements, species toxicity, and treatment
  history via typed relationships — something prompt-stuffing cannot do reliably.
- **Fails safely:** because access is **delegated / identity-based**, out-of-scope or unauthorized data
  yields a structural/authorization boundary, not a confident hallucination. *(verified-capabilities §1c.)*
- **Why it's a "contract":** the ontology is the agreed interface between the data platform and the agent;
  change models freely, the contract holds.
- **Claims-to-verify:** all clauses map to verified-capabilities §1/§2; preview status + date stated.

### 4b. HEADLINE #2 — Frontier model swappability / model independence (article §S9)
- **Claim:** swap the model via **config, not code** — a Foundry agent references a **model deployment by
  name**, so swapping is a config/deployment change. *(Art. III; verified-capabilities §2b.)*
- **The experiment:** use the optimizer's **model-selection** target
  (`options.optimization_config.model` list) to score the agent across deployments (e.g. a flagship vs a
  smaller/mini vs an open-weights model) and produce a **cost-vs-accuracy scorecard**, aiming to show a
  smaller optimized model *approaching* a flagship. *(verified-capabilities §3b.)*
- **Honesty guardrails:** (a) the model-selection sweep runs through the **gated** optimizer, so the
  fallback path applies (§S7 / #10); (b) **RESOLVED (Phase 7, 2026-07-08)** — the config-only swap produced
  **real** numbers: `gpt-5.4-mini` **87.5% (21/24)** vs flagship **91.7% (22/24)**, matching **within noise**
  (paired Δ 95% CI [−12.5, 0.0] includes 0; shared S01/M06 misses) at **~8× cheaper**, but **NOT a strict
  Pareto win** (state plainly). The finished article states this as fact with citation, no placeholder
  (`eval/showdown/RESULTS.md`); (c) supported `optimization_model` values — see verified-capabilities §3c
  (the earlier narrow list is superseded; the article does not enumerate it).
- **Claims-to-verify:** verified-capabilities §2b, §3b, §3c; results are Phase-7 outputs, not yet real.
- **Cross-vendor extension (EPIC H, model independence past the vendor boundary):** the same config-string-only
  swap that moves `gpt-5.4` → `gpt-5.4-mini` **within** the OpenAI family also crosses the **vendor boundary** to
  the **open-weights, non-GPT `Kimi-K2.6`** (Moonshot AI, GlobalStandard SKU) as the reasoning/answer model on
  the **identical, unmodified** harness. Measured result (`eval/showdown_xvendor/RESULTS.md`): **87.5% (21/24)**
  vs the `gpt-5.4` anchor **91.7% (22/24)**, **parity within noise** (paired Δ **−4.2 pts, 95% CI [−12.5, 0.0] —
  includes 0**, N=24), while **cheaper in USD on every axis** on the same GlobalStandard SKU ($/query $0.006345
  vs $0.006818; $/correct $0.007252 vs $0.007438); groundedness 100%, refusals 6/6; single shared config hash
  `f9a15da1…` = enshrined Phase-7 (only variable = the reasoning-model string). **Honesty guardrails:** state
  "parity within noise" / "statistically indistinguishable on this held-out set" — **never** "beats"/"proves";
  cost is a **USD-only** claim (Kimi and GPT use different tokenizers, so token counts are per-model
  informational only); **no** deployment-basis caveat (all GlobalStandard); note N=24 and that the anchor is
  itself a single run with retrieval variance. KB `answerSynthesis` staying on `gpt-5.4` is stated **factually
  as configuration** (a GPT-family-only platform surface, verified-capabilities §5c), **not** a limitation — the
  reasoning/answer model is Kimi-K2.6. Pre-registered in `docs/cross-vendor-protocol.md`.
- **Claims-to-verify:** `eval/showdown_xvendor/RESULTS.md`; verified-capabilities §5 (§5a catalog, §5b
  GlobalStandard pricing, §5c KB synthesis allow-list); `docs/cross-vendor-protocol.md` §5 success criteria.

---

## 5. Claims-to-verify callouts (accuracy register)

Every technical assertion in the finished article must carry an inline citation to a primary source (via
`docs/verified-capabilities.md`) and state preview/GA status + date (Art. I). Summary register:

| # | Article claim | Status | Source (in verified-capabilities.md) | Honesty flag |
| --- | --- | --- | --- | --- |
| C1 | Fabric IQ ontology models entities/relationships/properties + binds OneLake data without copying | `Verified-Preview` | §1 / §1a | State preview + date; note binding limits (managed tables, no OneLake security, no column mapping) |
| C2 | Agent grounds in Fabric IQ via the **Knowledge Base `/retrieve` + inject** path (native `fabric_iq_preview` tool disqualified 2026-07-08) | `Verified-by-test` | §2b / §2a | three grounding paths exist; we use the KB retrieve+inject path (§2b), not the native tool |
| C3 | NL2Ontology dispatches GQL (graph) / KQL (Eventhouse); graph needs tenant Graph setting | `Verified-Preview` | §1a | Manual graph refresh for new rows (G4) |
| C4 | Weights stay frozen; optimization is text/config only | `Verified-Preview` (by construction) | §2b / §3 | Central to Art. II — no weight-update step anywhere |
| C5 | Foundry Agent Optimizer: four targets, `eval.yaml` shape, score bands | `Gated` (preview + allow-list) | §3, §3a–§3c | **Prominent 403/allow-list flag (#10)**; `optimization_model` ∈ {gpt-5, gpt-5.1, gpt-5.3} only |
| C6 | SkillOpt = research anchor + drop-in fallback loop | `Verified-GA` | §4 | Attribute to Microsoft Research (Art. VII.2); arXiv:2605.23904, MIT repo |
| C7 | Model swappability = config-only deployment swap + model-selection sweep | `Verified-Preview` | §2b / §3b | **RESOLVED (Phase 7, 2026-07-08):** config-only swap → `gpt-5.4-mini` **87.5% (21/24)** vs flagship **91.7% (22/24)** at **~12% cost (~8× cheaper)**; within noise (paired Δ 95% CI [−12.5, 0.0] includes 0), **NOT a strict Pareto win**. Source: `eval/showdown/RESULTS.md`, `eval/scorecards/optimized_gpt-5.4-mini.*` |
| C8 | Auth = delegated user identity; RBAC Foundry User + Project Manager | `Verified-Preview` | §1c / §2a | Service-principal Entra scopes are **Unverified** (Corrections #7, G2) |
| C9 | Fabric IQ preview may incur cost / send data outside Azure compliance boundary | `Verified-Preview` | §2a | Real-data wiring gated behind approval (Art. VI/VII, G5); public demo uses synthetic fixtures |
| C10 | **Cross-vendor model independence** — the identical harness with the reasoning/answer model swapped (config string only) to the **open-weights, non-GPT `Kimi-K2.6`** reaches **parity within noise** vs the `gpt-5.4` anchor at **lower USD cost** (same GlobalStandard SKU) | `Verified-by-test` (EPIC H) | §5a / §5b / §5c (+ `eval/showdown_xvendor/RESULTS.md`, `docs/cross-vendor-protocol.md`) | **87.5% (21/24) vs 91.7% (22/24)**; paired Δ **−4.2 pts, 95% CI [−12.5, 0.0] includes 0** (N=24); USD $/query **$0.006345 vs $0.006818**, $/correct **$0.007252 vs $0.007438**; groundedness 100%, refusals 6/6; single config hash `f9a15da1…` = enshrined Phase-7. **Say "parity within noise", not "beats"/"proves"; USD-only cost claim (different tokenizers → token counts informational only); no deployment-basis caveat (all GlobalStandard); N=24, anchor is a single run.** KB `answerSynthesis` on `gpt-5.4` stated **factually as config** (GPT-only platform surface, §5c), not a limitation |

**Corrections to carry forward (do not reintroduce):** no `fabric_iq_connection` tool (use
`fabric_iq_preview`); "MCP vs native" is a false dichotomy (native tool is built on MCP); azd extension is
`azure.ai.agents` (not `microsoft.foundry`); dataset gen is `azd ai agent eval init` (not `eval generate`);
model-selection key is `options.optimization_config.model` (not `model_search`). *(verified-capabilities
Corrections #1–#8.)*

---

## 6. Publication plan

### Recommended venue: **Microsoft Tech Community (primary)** with a **dev.to cross-post (canonical link back)**

**Rationale:**
- **Microsoft Tech Community** is the natural home for a deep Fabric IQ + Foundry architecture piece: the
  audience (enterprise data/AI architects) already reads it, it lends credibility for a Microsoft-stack
  story, and it is appropriate for content that is careful to mark **preview** features. It best serves the
  two headline narratives to the people making platform decisions.
- **dev.to cross-post** widens reach to the broader developer community and renders the runnable-repo/code
  story well; set the **canonical URL** to the Tech Community post to avoid SEO duplication.
- **Personal blog** is the fallback/archival home (full editorial control, permanent canonical) if Tech
  Community's editorial/preview constraints are restrictive; it can also host the canonical copy with
  Tech Community + dev.to as syndicated cross-posts. Recommended only as secondary.

**Publication gate (Art. VIII):** venue selection here is a *recommendation only*. Nothing is published, and
the repo is **not** made public, without explicit user approval for that specific action. The repo stays
**private** until the publication approval gate.

**Scope note — Headline #2 now spans two results.** The model-independence headline (§4b / §S9) covers **both**
the within-GPT-family swap (Phase 7: `gpt-5.4` ↔ `gpt-5.4-mini`) **and** the **cross-vendor** extension (EPIC H:
the open-weights, non-GPT `Kimi-K2.6` at parity within noise and lower USD cost, `eval/showdown_xvendor/RESULTS.md`).
The cross-vendor write-up is part of Headline #2 and, like the rest of the article, stays behind the Art. VIII
publication gate.

### License restatement
- **Code: MIT.**
- **Prose / article: CC-BY.**
- (Per Constitution Art. VII.3; unchanged unless the user chooses otherwise.)

---

## 7. Consistency & governance checklist (for the drafting phase)

- [ ] Every technical assertion cites `docs/verified-capabilities.md` and states preview/GA + date (Art. I).
- [ ] No corrected PDF inaccuracy is reintroduced (see §5 corrections list).
- [ ] Non-parametric integrity (Art. II) and model independence (Art. III) are **central**, each with a
      dedicated section (§S5.5 / §4a and §S9 / §4b).
- [ ] Semantics live in the ontology, not prompts (Art. IV) — asserted and demonstrated.
- [ ] Optimizer allow-list gate (#10) and SkillOpt fallback are flagged **honestly and prominently** (§S7).
- [x] Cost/accuracy swappability numbers are **now real Phase-7 outputs** and stated as fact with citation
      (`eval/showdown/RESULTS.md`; scorecards) — no remaining placeholders. Framed honestly as within-noise /
      not-strict-Pareto.
- [ ] Repo stays private; publication + public-push are explicit approval gates (Art. VIII).
- [ ] Delivered as Issue #13 → PR, left unmerged for review (Art. XIII).
