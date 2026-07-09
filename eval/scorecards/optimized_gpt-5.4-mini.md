# Recommended (conservative injection) scorecard — `gpt-5.4-mini`

_Generated 2026-07-08T23:58:37.115986+00:00 · 24 tasks · ontology grounded in ALL runs._

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **87.5%** (21/24) |
| Tokens (total in/out) | 64410 / 2454 |
| Tokens (avg/task) | 2786.0 |
| Cost total (USD) | $0.021011 |
| Cost per correct answer (USD) | $0.001001 |
| Latency avg / p95 (ms) | 22871 / 27051 |
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
| S01 | single_hop | ❌ | ✔ | 1134/51 | 24423 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ✅ | ✔ | 1134/50 | 18830 | found 4.0 within tol of 4.0 |
| S03 | single_hop | ✅ | ✔ | 1184/65 | 16976 | recall 1.00 |
| S04 | single_hop | ✅ | ✔ | 1138/59 | 19379 | found 13.0 within tol of 13.0 |
| S05 | single_hop | ✅ | ✔ | 1149/56 | 18853 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ✅ | ✔ | 1164/88 | 20236 | found 88.67 within tol of 88.67 |
| S07 | single_hop | ✅ | ✔ | 1145/62 | 17902 | found 142.7 within tol of 142.7 |
| S08 | single_hop | ✅ | ✔ | 1246/92 | 18607 | found 8.0 within tol of 8.0 |
| M01 | multi_hop | ✅ | ✔ | 1770/126 | 20941 | recall 1.00 |
| M02 | multi_hop | ✅ | ✔ | 14380/203 | 74540 | recall 1.00 |
| M03 | multi_hop | ✅ | ✔ | 1497/93 | 21583 | recall 1.00 |
| M04 | multi_hop | ❌ | ✔ | 4685/541 | 26981 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| M05 | multi_hop | ✅ | ✔ | 1137/56 | 18921 | found 10.0 within tol of 10.0 |
| M06 | multi_hop | ❌ | ✔ | 1134/54 | 20862 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ✅ | ✔ | 1721/107 | 21260 | recall 1.00 |
| M08 | multi_hop | ✅ | ✔ | 1178/94 | 20331 | found 185.67 within tol of 185.67 |
| M09 | multi_hop | ✅ | ✔ | 1233/88 | 21426 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ✅ | ✔ | 7969/202 | 27051 | recall 1.00 |
| N01 | negative | ✅ | ✔ | 11232/71 | 26946 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 1720/55 | 17278 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1130/62 | 21322 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 1599/73 | 17741 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 1600/74 | 17376 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1131/32 | 19148 | refusal: judge-primary |
