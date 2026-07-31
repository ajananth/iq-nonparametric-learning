# Baseline scorecard — `kimi-k2.6`

_Generated 2026-07-31T01:22:37.549164+00:00 · 24 tasks · ontology grounded in ALL runs._

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **87.5%** (21/24) |
| Tokens (total in/out) | 90822 / 16501 |
| Tokens (avg/task) | 4471.8 |
| Cost total (USD) | $0.152285 |
| Cost per correct answer (USD) | $0.007252 |
| Latency avg / p95 (ms) | 28226 / 37457 |
| Grounded (called Fabric IQ) | 100.0% |
| Multi-hop traversal correct | 80.0% |
| Frozen weights / single config | True / True |

> Cost pricing verified: **False** (source: placeholder - replace with your Foundry/AOAI pricing).

## Accuracy by category

| Category | Correct | Total | % |
| --- | --- | --- | --- |
| multi_hop | 8 | 10 | 80.0% |
| negative | 6 | 6 | 100.0% |
| single_hop | 7 | 8 | 87.5% |

## Per-task

| id | cat | correct | grounded | in/out tok | ms | detail |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | single_hop | ❌ | ✔ | 1136/115 | 30386 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ✅ | ✔ | 1138/303 | 19163 | found 4.0 within tol of 4.0 |
| S03 | single_hop | ✅ | ✔ | 1185/716 | 23124 | recall 1.00 |
| S04 | single_hop | ✅ | ✔ | 1145/223 | 20367 | found 13.0 within tol of 13.0 |
| S05 | single_hop | ✅ | ✔ | 1154/297 | 19602 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ✅ | ✔ | 1169/332 | 29791 | found 88.67 within tol of 88.67 |
| S07 | single_hop | ✅ | ✔ | 1149/342 | 20622 | found 142.7 within tol of 142.7 |
| S08 | single_hop | ✅ | ✔ | 1144/274 | 18753 | found 8.0 within tol of 8.0 |
| M01 | multi_hop | ✅ | ✔ | 1773/1071 | 27207 | recall 1.00 |
| M02 | multi_hop | ✅ | ✔ | 39388/3151 | 64144 | recall 1.00 |
| M03 | multi_hop | ✅ | ✔ | 2245/749 | 33658 | recall 1.00 |
| M04 | multi_hop | ✅ | ✔ | 5125/924 | 37457 | recall 1.00 |
| M05 | multi_hop | ✅ | ✔ | 1142/295 | 28853 | found 10.0 within tol of 10.0 |
| M06 | multi_hop | ❌ | ✔ | 1139/317 | 27517 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ✅ | ✔ | 1987/1320 | 33104 | recall 1.00 |
| M08 | multi_hop | ✅ | ✔ | 1183/269 | 23346 | found 185.67 within tol of 185.67 |
| M09 | multi_hop | ✅ | ✔ | 1241/430 | 21669 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ❌ | ✔ | 7096/2116 | 32740 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| N01 | negative | ✅ | ✔ | 11702/762 | 35786 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 2104/609 | 28126 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1135/430 | 24688 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 1602/504 | 21488 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 1603/530 | 32223 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1137/422 | 23616 | refusal: judge-primary |
