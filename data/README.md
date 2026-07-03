# `data/` — Synthetic dataset (committable)

**Intent.** This directory holds the **synthetic** dataset for the water-utilities / algal-bloom demo.
Per **Constitution Art. V (Reproducibility)** the demo must run for any third party **without private/real
data**, so everything here is **fabricated, non-sensitive, and intentionally committed to the repo**.

> **This data is committable.** There is deliberately **no git-ignored `real/` slot** here. Real customer
> data is *never* committed and is wired only via config/environment in later phases (Art. V.3). The
> `.gitignore` ignores **secrets only** — it does **not** ignore `data/`.

**Status: placeholder — the actual synthetic fixtures are generated in Phase 3.** No runtime or file format
is committed to in Phase 2.

## Planned datasets (Phase 3)
The scenario spans three OneLake source shapes that the ontology will bind to:

1. **Telemetry stream** (→ Eventhouse, time-series/columnar): high-frequency sensor readings from monitoring
   stations.
2. **Lab assays** (→ Lakehouse managed table): periodic laboratory measurements.
3. **Assets / geospatial** (→ Lakehouse managed table): water sources, treatment plants, stations, topology.

## Draft schema notes (illustrative — finalised in Phase 3)

### `telemetry` (time-series)
| Column | Type | Notes |
| --- | --- | --- |
| `station_id` | string | FK → `assets.station_id` |
| `timestamp` | timestamp (UTC) | reading time |
| `phycocyanin_ugL` | double | cyanobacteria proxy pigment (µg/L) |
| `chlorophyll_a_ugL` | double | algal biomass proxy (µg/L) |
| `cell_count_per_mL` | double | cyanobacteria cell count |
| `turbidity_ntu` | double | nephelometric turbidity units |

### `lab_assays` (periodic)
| Column | Type | Notes |
| --- | --- | --- |
| `assay_id` | string | primary key |
| `station_id` | string | FK → `assets.station_id` |
| `sampled_at` | timestamp (UTC) | sample collection time |
| `geosmin_ngL` | double | taste-and-odour compound (ng/L) |
| `mib_ngL` | double | 2-methylisoborneol (ng/L) |
| `microcystin_ugL` | double | cyanotoxin (µg/L) |

### `assets` (static / geospatial)
| Column | Type | Notes |
| --- | --- | --- |
| `station_id` | string | primary key |
| `water_source_id` | string | FK → water source |
| `plant_id` | string | FK → treatment plant |
| `latitude` / `longitude` | double | station location |
| `pac_dosing_rate` | double | powdered activated carbon dosing rate |
| `storage_capacity_ML` | double | storage capacity (megalitres) |

Binding these to the ontology (Phase 4) must comply with the constraints in
`docs/verified-capabilities.md` §1a (managed tables; no OneLake security; no column mapping).
