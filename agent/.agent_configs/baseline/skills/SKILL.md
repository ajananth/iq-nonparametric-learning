# Skill: Algal-bloom investigation (baseline)

<!--
Phase 5 (issue #24, EPIC D #4). Open Agent Skills format (agentskills.io). Skill-improvement target for the
Agent Optimizer, which refines the skill BODY while leaving the description unchanged
(docs/verified-capabilities.md §3b). Loaded via load_config() so the same code runs with/without the
optimizer. Per Art. IV this skill guides the INVESTIGATION PROCESS in business terms; it does not encode
table/column names or SQL — the agent reaches all semantics through the fabric_iq_preview tool.
-->

## Description
Guide a structured, evidence-first investigation of algal-bloom risk and remediation for a water site,
grounded end-to-end in the Fabric IQ ontology.

## Body
When asked about bloom activity, water-quality conditions, the species involved, or treatments:

1. **Frame the question in business terms** and route it to the `fabric_iq_preview` tool. Identify the
   water site(s) in scope and, when the question spans concepts, the relationships you need the ontology to
   traverse — a site's water-quality measurements, a measurement's dominant algae species, and a site's
   treatment records.
2. **Retrieve the water-quality evidence** through the tool: readings such as chlorophyll-a, algal cell
   count, nutrients (nitrate, phosphate), turbidity, pH, and dissolved oxygen. Let the ontology return the
   values; do not assume them.
3. **Characterise the species** where a dominant algae species is present: its toxicity level, taxonomic
   group, and typical bloom triggers, so risk can be judged.
4. **Relate findings to treatments** applied at the site — method, outcome, and whether follow-up was
   required — to see what has and has not worked.
5. **Summarise risk and a recommended next action**, citing the specific sites, measurements, species, and
   treatment outcomes the ontology returned as evidence.

If the ontology lacks the data to answer, or the request is outside the water-quality domain, say so plainly
and state what is missing. Never invent entities, values, or relationships.
