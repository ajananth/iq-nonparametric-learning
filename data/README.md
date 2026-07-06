# `data/` — Synthetic dataset (committable)

> **Issue:** #20 (EPIC C, #3) · **Phase:** 3 (domain & data model — authoring only, no live Fabric)

**Intent.** This directory holds the **synthetic** dataset for the water-utilities / algal-bloom demo.
Per **Constitution Art. V (Reproducibility)** the demo must run for any third party **without private/real
data**, so everything here is **fabricated, non-sensitive, and intentionally committed to the repo**.

> **This data is committable.** There is deliberately **no git-ignored `real/` slot** here. Real customer
> data is *never* committed and is wired only via config/environment in later phases (Art. V.3). The
> `.gitignore` ignores **secrets only** — it does **not** ignore `data/`.

## Provenance & licensing

- **Derived from:** [`ajananth/water-quality-assistant`](https://github.com/ajananth/water-quality-assistant),
  path `data-seeder/data/`. The 4 CSVs here are **vendored verbatim** from that repo.
- **Nature:** fully **synthetic / AI-generated**, **non-sensitive** data modelling a Southeast Queensland
  (Australia) water-utility algal-bloom scenario. No real customer, personal, or operational data.
- **Real IDs:** the `*_id` values (UUIDv5-style strings, small integers) are part of the synthetic data and
  are safe to commit. **No secrets, tokens, keys, or connection strings** appear here (Constitution Art. VI).
- **License:** code in this repo is **MIT**; prose/documentation is **CC-BY** (Constitution Art. VII.3).

## The 4 tables (real schema — CSV headers are authoritative, Constitution Art. I)

Each CSV loads **flat** (no medallion, no transforms) into one **managed Delta table** of the same stem name
in a Fabric Lakehouse (default display name **`iqnpl_lakehouse`**, created by `scripts/load_lakehouse.py`). The
ontology (`ontology/`) binds these tables to entity types and relationships.

### `sites.csv` → table `sites` (20 rows) — entity **Site**
| Column | Type | Notes |
| --- | --- | --- |
| `site_id` | string (UUID) | **primary key** |
| `site_name` | string | display name |
| `water_body_type` | string | e.g. `reservoir`, `wetland`, `coastal_bay_lagoon` |
| `region` | string | |
| `country` | string | |
| `latitude` | double | |
| `longitude` | double | |
| `active` | string (`true`/`false`) | boolean stored as text (see note) |
| `established_year` | bigint | |

### `algae_species.csv` → table `algae_species` (50 rows) — entity **AlgaeSpecies**
| Column | Type | Notes |
| --- | --- | --- |
| `species_id` | string (UUID) | **primary key** |
| `scientific_name` | string | |
| `common_name` | string | |
| `phylum` | string | e.g. `Cyanobacteria` |
| `toxicity_level` | string | `low` / `moderate` / `high` |
| `bloom_trigger_conditions` | string | free text |
| `notes` | string | free text |

### `water_quality_measurements.csv` → table `water_quality_measurements` (200 rows) — entity **WaterQualityMeasurement**
| Column | Type | Notes |
| --- | --- | --- |
| `measurement_id` | string (UUID) | **primary key** |
| `site_id` | string (UUID) | **FK → `sites.site_id`** |
| `recorded_at` | datetime (ISO 8601) | reading time |
| `ph` | double | |
| `dissolved_oxygen_mgl` | double | mg/L |
| `turbidity_ntu` | double | NTU |
| `chlorophyll_a_ugl` | double | µg/L — algal biomass proxy |
| `nitrate_mgl` | double | mg/L |
| `phosphate_mgl` | double | mg/L |
| `algae_cell_count_cells_ml` | bigint | cells/mL |
| `dominant_species_id` | string (UUID) | **FK → `algae_species.species_id`** (nullable — blank when no bloom) |
| `notes` | string | free text |

### `treatment_records.csv` → table `treatment_records` (80 rows) — entity **TreatmentRecord**
| Column | Type | Notes |
| --- | --- | --- |
| `treatment_id` | string (UUID) | **primary key** |
| `site_id` | string (UUID) | **FK → `sites.site_id`** |
| `treatment_date` | date | |
| `method` | string | e.g. algaecide, aeration, clay flocculation |
| `dosage_or_description` | string | free text |
| `outcome` | string | e.g. `successful` / `partial` |
| `follow_up_required` | string (`true`/`false`) | boolean stored as text (see note) |
| `notes` | string | free text |

## Relationships (foreign keys → ontology graph edges)

- `water_quality_measurements.site_id` → `sites.site_id`  (Site **hasMeasurement** WaterQualityMeasurement)
- `treatment_records.site_id` → `sites.site_id`  (Site **hasTreatment** TreatmentRecord)
- `water_quality_measurements.dominant_species_id` → `algae_species.species_id`  (WaterQualityMeasurement **dominantSpecies** AlgaeSpecies)

See [`ontology/README.md`](../ontology/README.md) for how these become typed, directional graph edges.

## Notes & flags

- **No medallion.** These CSVs are loaded flat, one managed Delta table each — no Bronze/Silver/Gold, no
  transforms (issue #20 constraint).
- **Booleans as text.** `active` and `follow_up_required` are the literal strings `true`/`false` in the source
  CSVs and are modelled as `String` in the ontology (see `ontology/README.md`) to stay faithful to the source
  and avoid an unverified ontology `valueType`. This is a deliberate, flagged fidelity choice, not a data fix.
- **Binding constraints (Phase 4).** Binding these tables to the ontology must comply with
  [`docs/verified-capabilities.md`](../docs/verified-capabilities.md) §1a: Lakehouse tables must be
  **managed**, **no** OneLake security, **no** column mapping; upstream row changes need a **manual graph
  refresh**.
