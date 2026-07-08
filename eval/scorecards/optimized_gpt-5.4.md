# Recommended (conservative injection) scorecard — `gpt-5.4`

_Generated 2026-07-08T07:53:01.237082+00:00 · 24 tasks · ontology grounded in ALL runs._

> **Phase-6 RECOMMENDED config** (`agent/.agent_configs/optimized/`): baseline knowledge base UNCHANGED
> (reasoning=medium, no custom retrieval/answer instructions) + a single client-side injection edit —
> drop the 8 redundant `*_json` graph-serialization columns. Retrieval is byte-identical to the Phase-5
> baseline (single-variable); the only diff vs baseline is `injection.json`. Held-out 24-Q result: accuracy
> **held at 91.7% (22/24)** with tokens lower (see `../optimization_runs/20260708T064838Z/RESULTS.md`).

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **91.7%** (22/24) |
| Tokens (total in/out) | 97226 / 4211 |
| Tokens (avg/task) | 4226.5 |
| Cost total (USD) | $0.163643 |
| Cost per correct answer (USD) | $0.007438 |
| Latency avg / p95 (ms) | 46848 / 83940 |
| Grounded (called Fabric IQ) | 100.0% |
| Multi-hop traversal correct | 90.0% |
| Frozen weights / single config | True / True |

> Cost pricing verified: **False** (source: placeholder - replace with your Foundry/AOAI pricing).

## Accuracy by category

| Category | Correct | Total | % |
| --- | --- | --- | --- |
| multi_hop | 9 | 10 | 90.0% |
| negative | 6 | 6 | 100.0% |
| single_hop | 7 | 8 | 87.5% |

## Per-task

| id | cat | correct | grounded | in/out tok | ms | detail |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | single_hop | ❌ | ✔ | 1132/45 | 83940 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ✅ | ✔ | 1134/39 | 50001 | found 4.0 within tol of 4.0 |
| S03 | single_hop | ✅ | ✔ | 1182/67 | 52364 | recall 1.00 |
| S04 | single_hop | ✅ | ✔ | 1140/48 | 48738 | found 13.0 within tol of 13.0 |
| S05 | single_hop | ✅ | ✔ | 1149/40 | 47742 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ✅ | ✔ | 1161/64 | 49959 | found 88.67 within tol of 88.67 |
| S07 | single_hop | ✅ | ✔ | 1145/49 | 43477 | found 142.7 within tol of 142.7 |
| S08 | single_hop | ✅ | ✔ | 1140/51 | 34785 | found 8.0 within tol of 8.0 |
| M01 | multi_hop | ✅ | ✔ | 1765/439 | 58135 | recall 1.00 |
| M02 | multi_hop | ✅ | ✔ | 6458/668 | 107181 | recall 1.00 |
| M03 | multi_hop | ✅ | ✔ | 1499/180 | 36540 | recall 1.00 |
| M04 | multi_hop | ✅ | ✔ | 15560/639 | 67682 | recall 1.00 |
| M05 | multi_hop | ✅ | ✔ | 1137/46 | 25359 | found 10.0 within tol of 10.0 |
| M06 | multi_hop | ❌ | ✔ | 1134/59 | 30271 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ✅ | ✔ | 1895/429 | 41797 | recall 1.00 |
| M08 | multi_hop | ✅ | ✔ | 1180/75 | 49519 | found 185.67 within tol of 185.67 |
| M09 | multi_hop | ✅ | ✔ | 1247/94 | 26832 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ✅ | ✔ | 31362/666 | 74034 | recall 1.00 |
| N01 | negative | ✅ | ✔ | 17505/127 | 57132 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 1720/94 | 26348 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1130/61 | 32188 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 1720/95 | 26566 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 1600/78 | 26406 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1131/58 | 27362 | refusal: judge-primary |
