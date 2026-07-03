# `ontology/` — Fabric IQ ontology definitions (Phase 3/4)

**Intent.** This directory will hold the source-controlled definition of the **Fabric IQ ontology
(preview)** for the water-utilities / algal-bloom scenario: entity types, properties, relationships,
constraints, and the data-binding specifications that map them to OneLake sources.

**Status: placeholder — deliverables land in Phase 3 (domain & data model) and Phase 4 (ontology build).**
Nothing is authored here in Phase 2.

## Planned contents (Phase 3/4)
- Entity types: `WaterSource`, `WaterTreatmentPlant`, `AlgalMonitoringStation`, `WaterQualityMetric`.
- Relationships: `monitors`, `supplies`, `records` (typed, directional, with cardinality/attributes).
- Properties: Phycocyanin, Chlorophyll-a, Geosmin, MIB, cell count, PAC dosing rate, storage, capacity.
- Data-binding specs against OneLake (Eventhouse telemetry, Lakehouse lab reports, asset tables).

## Constraints to honour (from `docs/verified-capabilities.md` §1a)
- Lakehouse tables must be **managed**, with **no OneLake security** and **no column mapping**.
- Upstream row changes require a **manual graph refresh**.
- The **Graph in Microsoft Fabric** tenant setting must be enabled for graph traversal.

Per **Art. IV**, schema and business vocabulary live here in the ontology — never baked into agent prompts.
