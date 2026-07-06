# `scripts/` — Phase 3 authoring (write now, run in Phase 4)

> **Issue:** #20 (EPIC C, #3) · **Phase:** 3 (authoring only)

**Intent.** Automation to stand up the demo's data + semantic layer. Per issue #20 these scripts are
**authored in Phase 3 but not executed** — live application against Fabric/OneLake happens in **Phase 4**,
behind the Constitution Art. VIII human-in-the-loop gate. Nothing here touches live Azure/Fabric when merged.

All scripts are **env/param-driven** and commit **no secrets, tokens, or workspace/item GUIDs**
(Constitution Art. VI). Configuration comes from environment variables (see [`../.env.example`](../.env.example))
or CLI flags. Auth uses `DefaultAzureCredential` (delegated identity — `docs/verified-capabilities.md` §1c).

## Scripts

| Script | Phase | What it does |
| --- | --- | --- |
| `load_lakehouse.py` | 4 | **Flat** load: writes each of the 4 vendored CSVs in `data/` directly as a **managed Delta table** (`Tables/<name>`) in a Fabric Lakehouse via `deltalake` (delta-rs). Creates the Lakehouse via REST if `FABRIC_LAKEHOUSE_ID` is unset (default display name **`iqnpl_lakehouse`**, override with `--lakehouse-name`). **No medallion, no transforms** (issue #20). |
| `create_ontology_item.py` | 4 | Creates a **new empty Fabric IQ Ontology (preview) item** (default display name **`iqnpl_ontology`**) via Fabric REST `POST /workspaces/{ws}/items` with `type: "Ontology"` (verified against the Item Management overview, `updated_at` 2026-06-18), polling the create LRO and printing the new **ontology item GUID** to feed into `deploy_ontology.py`. Portal creation is the documented fallback. |
| `deploy_ontology.py` | 4 | Assembles the `ontology/` part files into an `updateDefinition?beta=true` `parts` array (substituting `${FABRIC_WORKSPACE_ID}` / `${FABRIC_LAKEHOUSE_ID}`), base64-encodes them, and applies them to the ontology (preview) item. `--dry-run` validates locally without calling Fabric. |
| `build_graph_model.py` | 4 | **Builds the companion GraphModel programmatically** (no portal Save). Projects the deployed `ontology/` tree into the GraphModel's `graphType` / `dataSources` / `graphDefinition` / `stylingConfiguration` parts, applies them via the GraphModel item's `updateDefinition`, and (`--refresh`) triggers a `RefreshGraph` job to ingest data. Required because ontology `updateDefinition` does **not** auto-build the graph (`docs/verified-capabilities.md` §1d). `--dry-run` prints the assembled parts without calling Fabric. |

Later phases will add eval/optimizer automation (Phase 6) — not authored here. The manual **graph refresh**
(`docs/verified-capabilities.md` §1a) is handled by `build_graph_model.py --refresh` (or a standalone
`RefreshGraph` job).

## Usage (Phase 4 — do not run in Phase 3)

```bash
pip install -r requirements.txt

# 1) Flat-load the managed Delta tables (creates `iqnpl_lakehouse`; prints the Lakehouse ID to reuse)
python scripts/load_lakehouse.py --workspace-id <ws-guid> [--lakehouse-id <lh-guid>]

# 2) Create a new empty Ontology (preview) item `iqnpl_ontology` (prints the ontology item GUID)
python scripts/create_ontology_item.py --workspace-id <ws-guid> [--display-name iqnpl_ontology]

# 3) Validate the ontology parts locally (safe; no Fabric call)
python scripts/deploy_ontology.py --dry-run

# 4) Deploy the ontology definition + bindings
python scripts/deploy_ontology.py \
    --workspace-id <ws-guid> --lakehouse-id <lh-guid> --ontology-item-id <ont-guid>

# 5) Build the companion GraphModel + refresh (programmatic; required for NL2Ontology/GQL queries)
python scripts/build_graph_model.py \
    --workspace-id <ws-guid> --lakehouse-id <lh-guid> --ontology-item-id <ont-guid> --refresh
```

## Reference patterns (adapted, not copied)

- **Flat load** — `ajananth/water-quality-assistant` `data-seeder/` (`seed_data.py`, `fabric/lakehouse.py`,
  `fabric/uploader.py`).
- **Ontology deploy** — `ajananth/research-iq` `scripts/setup_ontology.py` (the `updateDefinition` parts
  shape). **Pattern only** — that repo's hardcoded tenant/workspace/item GUIDs are **not** reused here; ours
  are env/param-driven.

See `docs/plan.md` for the full phase breakdown.
