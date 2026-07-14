# Phase 4 — LIVE Fabric deployment record

> **Issue:** #22 (EPIC C, #3) · **Deployment date:** **2026-07-06** · **Mode:** live, interactive
> **Author:** Phase 4 child session · **Governs:** Constitution Art. I (Accuracy), Art. VI (Secrets),
> Art. VIII (Human-in-the-loop), Art. XIII (Epic→Issue→PR).

This is the concrete, verified-by-test record of the live Fabric IQ deployment. It captures the real
infrastructure GUIDs (permitted per the narrowed Art. VI rule — infra GUIDs MAY be committed; **auth
tokens / keys / connection secrets MUST NOT**), the loaded row counts, and the end-to-end NL2Ontology
validation query and its result. Empirical capability findings are folded into
[`verified-capabilities.md` §1d](./verified-capabilities.md).

## Environment

| Item | Value |
| --- | --- |
| Tenant | `<tenant-id>` |
| Workspace (display name) | `iq-npl` |
| Workspace GUID | `<workspace-id>` |
| Capacity | `<capacity-id>` — **F64 (F-SKU)**, Active, Australia East |
| Tenant setting | **Enable Ontology item (preview)** = ON (only setting required — see §1d) |
| Auth | `az login` → `DefaultAzureCredential` (delegated user identity; no secrets stored) |

## Deployed resources

| Resource | Display name | GUID |
| --- | --- | --- |
| Lakehouse (data) | `iqnpl_lakehouse` | `<lakehouse-id>` |
| Ontology (preview) | `iqnpl_ontology` | `<ontology-item-id>` |
| GraphModel (companion, auto-created) | `iqnpl_ontology_graph_…` | `<graph-item-id>` |
| Lakehouse (companion, auto-created) | `iqnpl_ontology_lh_…` | `<companion-lakehouse-id>` |

## Loaded managed Delta tables (in `iqnpl_lakehouse`)

Flat load, no medallion, no transforms — one managed Delta table per source CSV.

| Table | Rows |
| --- | --- |
| `sites` | 20 |
| `algae_species` | 50 |
| `water_quality_measurements` | 200 |
| `treatment_records` | 80 |

## Ontology model (deployed)

- **Entities (4):** `Site` (`1001…`), `AlgaeSpecies` (`1002…`), `WaterQualityMeasurement` (`1003…`),
  `TreatmentRecord` (`1004…`) — each bound to the managed Delta table of the same name.
- **Relationships (3):**
  - `Site —hasMeasurement→ WaterQualityMeasurement` (via `water_quality_measurements.site_id`)
  - `Site —hasTreatment→ TreatmentRecord` (via `treatment_records.site_id`)
  - `WaterQualityMeasurement —dominantSpecies→ AlgaeSpecies` (via `water_quality_measurements.dominant_species_id`)

## Reproducible deployment steps

```bash
# 0. Authenticate (interactive; user runs this in the terminal)
az login
az account set --subscription <sub>   # if needed

# 1. Create Lakehouse + flat-load the 4 CSVs as managed Delta tables
python scripts/load_lakehouse.py --workspace-id <workspace-id>
#   -> capture the printed lakehouse GUID as FABRIC_LAKEHOUSE_ID

# 2. Create the ontology (preview) item
python scripts/create_ontology_item.py --workspace-id <ws> --display-name iqnpl_ontology
#   -> capture the printed ontology item GUID as FABRIC_ONTOLOGY_ITEM_ID

# 3. Deploy the ontology definition (entities + relationships + bindings)
python scripts/deploy_ontology.py --dry-run     # confirm placeholders resolve
python scripts/deploy_ontology.py --ontology-item-id <ont>

# 4. Build the companion GraphModel + refresh (programmatic — no portal Save needed)
python scripts/build_graph_model.py \
    --workspace-id <ws> --lakehouse-id <lh> --ontology-item-id <ont> --refresh
```

> **Note (empirical, see §1d):** step 4 is required because ontology `updateDefinition` does **not**
> auto-build the companion GraphModel — without it the graph is empty and NL2Ontology queries fail.
> `scripts/build_graph_model.py` performs the projection + `RefreshGraph` programmatically, so the whole
> pipeline runs with **no manual portal step**.

## Validation — NL2Ontology graph traversal (evidence)

Executed against the ontology MCP endpoint
(`…/v1/mcp/dataPlane/workspaces/{ws}/items/{ont}/ontologyEndpoint`) after the graph build + refresh.

**Query (natural language):**

> *"Which sites have the highest chlorophyll-a measurements, what are their dominant algae species, and what
> treatments were applied at those sites?"*

This single question exercises the full multi-hop traversal
`Site → hasMeasurement → WaterQualityMeasurement → dominantSpecies → AlgaeSpecies` **and**
`Site → hasTreatment → TreatmentRecord`.

**Result (top rows, abridged):** NL2Ontology resolved the question to a graph query returning fields
`[site_name, chlorophyll_a_ugl, dominant_scientific_name, dominant_common_name, treatment_method, treatment_outcome]`:

| Site | chlorophyll-a (µg/L) | Dominant species | Treatments (method → outcome) |
| --- | --- | --- | --- |
| Rotorua Drinking Catchment | 312.69 | *Spirogyra spp.* (Water silk) | nutrient reduction → ongoing; mechanical aeration → partial; UV treatment → successful; algaecide (copper sulfate) → successful |
| Moreton Bay North | 309.88 | *Noctiluca scintillans* (Sea sparkle) | manual removal (skimming) → successful; algaecide (copper sulfate) → partial; nutrient reduction → partial; clay flocculation → successful |
| Lake Rotorua Central | 303.52 | *Cyclotella meneghiniana* (Small centric diatom) | mechanical aeration → successful; clay flocculation → successful; algaecide (copper sulfate) → partial; barley straw application → successful |
| Lake Champlain South Bay | 303.41 | *Cylindrospermopsis raciborskii* | manual removal (skimming) → successful; barley straw application → unsuccessful; algaecide (copper sulfate) → partial; mechanical aeration → successful |
| Warragamba Dam Forebay | 302.01 | *Spirogyra spp.* (Water silk) | UV treatment → successful; mechanical aeration → partial; clay flocculation → successful; nutrient reduction → ongoing |

The result correctly joins measurements to their dominant species and to per-site treatment records,
confirming the managed-Delta bindings and all three relationships resolve end to end over the live graph.
