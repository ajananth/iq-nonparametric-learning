# Reproduction guide — reproduce the scorecards from scratch

> **Issue:** #33 (EPIC G, #7) · **Phase:** 8 · Spoke of the root [`README.md`](../README.md).
> **Source of truth for every capability claim:** [`docs/verified-capabilities.md`](./verified-capabilities.md)
> (preview/GA + dates). Prerequisites live in [`PREREQUISITES.md`](../PREREQUISITES.md) — read it first.

This guide reproduces the three enshrined runs behind the article:

| Run | Model | Config | Scorecard |
| --- | --- | --- | --- |
| Baseline-LLM (Phase 5) | `gpt-5.4` | `agent/.agent_configs/baseline/` | `eval/scorecards/baseline_gpt-5.4.*` |
| Optimized-LLM (Phase 6) | `gpt-5.4` | `agent/.agent_configs/optimized/` | `eval/scorecards/optimized_gpt-5.4.*` |
| Optimized-SLM (Phase 7) | `gpt-5.4-mini` | `agent/.agent_configs/optimized/` (identical) | `eval/scorecards/optimized_gpt-5.4-mini.*` |

> **⚠️ Cost gate (Constitution Art. VIII).** Every live rollout issues **real, billable** model + Fabric IQ
> calls, and provisioning **F2+** Fabric capacity accrues charges. Live steps below are **cost-gated**
> (`--confirm-cost`). You can validate the entire harness **offline for free** with the `--dry-run*` flags —
> see [§8](#8-offline-validation-no-azure-no-cost). No secrets are ever committed; auth is acquired at runtime
> via `DefaultAzureCredential` (`az login`).

---

## 0. What you need

See [`PREREQUISITES.md`](../PREREQUISITES.md) for the full, cited list. In brief: a paid **F2+** Fabric
capacity with the **Ontology (preview)** + **Graph in Microsoft Fabric** tenant settings; a **Foundry
project** with a **GPT-5-family** deployment (e.g. `gpt-5.4`, and `gpt-5.4-mini` for the swap); RBAC **Foundry
User** + **Foundry Project Manager**; **Python 3.10+**, **azd 1.21.3+** with the `azure.ai.agents` extension,
Azure CLI, `git`, and `gh`. The **Agent Optimizer** is allow-list gated (#10) — this repo ships a
**SkillOpt-style** fallback loop so you don't need it.

## 1. Clone & environment

```bash
git clone https://github.com/ajananth/iq-nonparametric-learning.git
cd iq-nonparametric-learning

python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt

az login                       # delegated identity — no secrets stored
cp .env.example .env           # fill in your Foundry/Fabric IDs (git-ignored; never committed)
```

Populate `.env` from your own tenant (see [`.env.example`](../.env.example) for every key): the Foundry
project endpoint + model deployment name, the Fabric workspace / lakehouse / ontology item IDs, the Fabric IQ
project connection ID, and the Azure AI Search endpoint. **Real values live only in your local `.env`.**

## 2. Provision the data + semantic layer (live; one-time)

Loads the **synthetic** fixtures in [`data/`](../data/README.md) and stands up the ontology from
[`ontology/`](../ontology/README.md). Each script is `--dry-run`-capable to validate locally first.

```bash
# a) Flat-load the 4 CSVs as managed Delta tables (creates `iqnpl_lakehouse`; prints the Lakehouse ID)
python scripts/load_lakehouse.py --workspace-id <ws-guid>

# b) Create an empty Ontology (preview) item (prints the ontology item GUID)
python scripts/create_ontology_item.py --workspace-id <ws-guid>

# c) Validate ontology parts locally, then deploy the definition + bindings
python scripts/deploy_ontology.py --dry-run
python scripts/deploy_ontology.py --workspace-id <ws-guid> --lakehouse-id <lh-guid> --ontology-item-id <ont-guid>

# d) Build the companion GraphModel + refresh (required for NL2Ontology / GQL traversal)
python scripts/build_graph_model.py --workspace-id <ws-guid> --lakehouse-id <lh-guid> \
    --ontology-item-id <ont-guid> --refresh
```

> New/changed rows require a **manual graph refresh** (`build_graph_model.py --refresh`) — a documented Fabric
> IQ preview constraint (verified-capabilities §1a).

## 3. Provision the grounding knowledge base (live; one-time)

The proven grounding surface is the **Foundry IQ Knowledge Base** (`fabricOntology`, agentic retrieval). It
returns verbatim ontology rows via `/retrieve`, which the harness injects into the agent context
(verified-capabilities §2b/§2c).

```bash
python scripts/provision_knowledge_base.py --model gpt-5.4 --dry-run   # print bodies, no live calls
python scripts/provision_knowledge_base.py --model gpt-5.4             # provision (synthesis model = gpt-5.4)
```

Smoke-test the grounded agent (swap the model freely — that is the whole point):

```bash
python agent/harness.py --model gpt-5.4      --prompt "How many monitored sites are active?"
python agent/harness.py --model gpt-5.4-mini --prompt "How many monitored sites are active?"
```

## 4. Baseline scorecard — Phase 5 (`gpt-5.4`)

First regenerate the deterministic ground truth **offline** (DuckDB over the CSVs — no Azure), then score:

```bash
python eval/ground_truth.py                          # writes eval/ground_truth.json (offline, free)
python eval/ground_truth.py --check                  # fails if the committed file is stale

python eval/scorer.py --model gpt-5.4 --dry-run-mock # offline dress-rehearsal, no cost
python eval/scorer.py --model gpt-5.4                # LIVE, cost-gated → scorecards/baseline_gpt-5.4.*
```

Expected: **91.7% (22/24)** · 107,450 tokens · $0.175350 · $0.007970/correct · 100% grounded ·
single-hop 7/8 · multi-hop 9/10 · negative 6/6.

## 5. Optimization loop — Phase 6 (`gpt-5.4`)

Run the SkillOpt-style loop (`rollout → reflect → held-out validate → adopt iff strictly better`). Validate
offline first, then run live:

```bash
python scripts/optimize_harness.py --dry-run --max-steps 3            # offline: candidates + diffs, no cost
python scripts/optimize_harness.py --confirm-cost --max-steps 12      # LIVE, cost-gated
```

The **adopted** recommended harness lands in `agent/.agent_configs/optimized/` — it drops the 8 redundant
`*_json` graph-serialization columns from the injected rows (a mechanism-justified, accuracy-safe injection
trim; see [`eval/optimization_runs/20260708T064838Z/RESULTS.md`](../eval/optimization_runs/20260708T064838Z/RESULTS.md)
for why the naïve DEV winner `c06` was **rejected** for overfitting). Score it:

```bash
python eval/scorer.py --model gpt-5.4                # → scorecards/optimized_gpt-5.4.*
```

Expected: **91.7% (22/24)** held exactly · 101,437 tokens · $0.163643 · $0.007438/correct. The controlled
(identical-rows) input-token reduction is **~40%**; the raw single-run net (−5.6%) is masked by
retrieval-volume noise.

## 6. Model swap — Phase 7 (`gpt-5.4-mini`)

Run the **exact same** optimized harness with **only the deployment string changed** (config-only swap; agent
**and** KB synthesis both become `gpt-5.4-mini`). Re-provision the KB to swap only the synthesis model, run,
then restore:

```bash
python scripts/provision_knowledge_base.py --model gpt-5.4-mini      # swap synthesis model only
python eval/scorer.py --model gpt-5.4-mini                           # → scorecards/optimized_gpt-5.4-mini.*
python scripts/provision_knowledge_base.py --model gpt-5.4           # restore canonical synthesis model
```

Expected: **87.5% (21/24)** · 66,864 tokens · $0.021011 · $0.001001/correct. The single shared config hash
(`f9a15da1…`, `fine_tuning=false`) makes the model deployment string the **sole** variable — the
model-independence proof (Art. III). See [`eval/showdown/RESULTS.md`](../eval/showdown/RESULTS.md) for the
within-noise analysis (paired Δ 95% CI includes 0) and the shared S01/M06 misses.

## 7. Regenerate the charts (offline, free)

```bash
python scripts/make_charts.py            # writes docs/assets/*.png from the committed scorecards
python scripts/make_charts.py --check    # verify the committed PNGs are present
```

The charts read `eval/scorecards/*.json` + `eval/showdown/RESULTS.md`, so they match the scorecards exactly.

## 8. Offline validation (no Azure, no cost)

Every stage has a free dress-rehearsal — useful in CI or before requesting cost approval:

```bash
python eval/ground_truth.py --check                        # ground truth is reproducible & current
python eval/scorer.py --model gpt-5.4 --dry-run-mock        # scorer wiring, canned answers
python eval/run_baseline.py --dry-run-mock                  # full matrix, no live calls
python scripts/optimize_harness.py --dry-run --max-steps 3  # optimizer loop with stub edits
python scripts/provision_knowledge_base.py --model gpt-5.4 --dry-run
python scripts/deploy_ontology.py --dry-run
python scripts/make_charts.py                               # charts from committed data
```

---

## Plug in your own data / ontology

The harness is data-agnostic. To point it at **your** domain:

1. Replace the CSVs in [`data/`](../data/README.md) with your own (keep one flat table per entity; real data
   is wired via config and **never** committed — Art. V).
2. Edit the declarative ontology under [`ontology/`](../ontology/README.md) — entity types, properties (=
   your columns), and relationship contextualizations (= your foreign keys).
3. Re-run [§2](#2-provision-the-data--semantic-layer-live-one-time)–[§3](#3-provision-the-grounding-knowledge-base-live-one-time),
   update `eval/dataset.jsonl` with your questions, regenerate the ground truth, and score.

Everything downstream — the optimizer loop, the model swap, the scorecards, the charts — is unchanged. That
is the point: **semantics live in the ontology, the model lives in config.**
