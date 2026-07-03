# Skill: Algal-bloom investigation (baseline — placeholder)

<!--
PLACEHOLDER skill in the open Agent Skills format (agentskills.io). This is the Skill-improvement target
for the Agent Optimizer, which refines the skill BODY (this content) while leaving the description unchanged
(docs/verified-capabilities.md §3b). Loaded via load_config() so the same code runs with/without the
optimizer. Real skills authored in Phase 5, optimized in Phase 6.
-->

## Description
Guide a structured investigation of algal-bloom risk for a water utility using the Fabric IQ ontology.

## Body
When asked about bloom risk or taste-and-odour events:

1. Identify the relevant `AlgalMonitoringStation`(s) and the `WaterSource` / `WaterTreatmentPlant` they
   relate to, via the ontology relationships (`monitors`, `supplies`).
2. Retrieve recent `WaterQualityMetric` readings — phycocyanin, chlorophyll-a, cell count (telemetry) and
   Geosmin, MIB, microcystin (lab assays) — through the `fabric_iq_preview` tool.
3. Correlate rising pigment/cell-count trends with taste-and-odour compounds and any cyanotoxin exceedances.
4. Relate findings to operational levers (e.g. PAC dosing rate, storage/capacity) available on the assets.
5. Summarise risk and a recommended action, citing the specific entities and metrics used as evidence.

Never invent table/column names or values; if the ontology lacks the data, say so.
