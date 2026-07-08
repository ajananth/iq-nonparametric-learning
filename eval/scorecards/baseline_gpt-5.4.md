# Baseline scorecard — `gpt-5.4`

_Generated 2026-07-08T04:26:29.592893+00:00 · 24 tasks · ontology grounded in ALL runs._

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **91.7%** (22/24) |
| Tokens (total in/out) | 102760 / 4690 |
| Tokens (avg/task) | 4477.1 |
| Cost total (USD) | $0.17535 |
| Cost per correct answer (USD) | $0.00797 |
| Latency avg / p95 (ms) | 30002 / 49498 |
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
| S01 | single_hop | ❌ | ✔ | 1132/46 | 35889 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ✅ | ✔ | 1134/45 | 24650 | found 4.0 within tol of 4.0 |
| S03 | single_hop | ✅ | ✔ | 1185/76 | 21619 | recall 1.00 |
| S04 | single_hop | ✅ | ✔ | 1136/53 | 28053 | found 13.0 within tol of 13.0 |
| S05 | single_hop | ✅ | ✔ | 1149/72 | 24322 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ✅ | ✔ | 1161/68 | 26495 | found 88.67 within tol of 88.67 |
| S07 | single_hop | ✅ | ✔ | 1145/50 | 23532 | found 142.7 within tol of 142.7 |
| S08 | single_hop | ✅ | ✔ | 1244/103 | 26586 | found 8.0 within tol of 8.0 |
| M01 | multi_hop | ✅ | ✔ | 1765/408 | 28861 | recall 1.00 |
| M02 | multi_hop | ✅ | ✔ | 8561/742 | 49498 | recall 1.00 |
| M03 | multi_hop | ✅ | ✔ | 1471/174 | 38672 | recall 1.00 |
| M04 | multi_hop | ✅ | ✔ | 37873/656 | 52864 | recall 1.00 |
| M05 | multi_hop | ✅ | ✔ | 1137/52 | 23898 | found 10.0 within tol of 10.0 |
| M06 | multi_hop | ❌ | ✔ | 1134/82 | 24626 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ✅ | ✔ | 5245/196 | 27091 | recall 1.00 |
| M08 | multi_hop | ✅ | ✔ | 1178/81 | 24796 | found 185.67 within tol of 185.67 |
| M09 | multi_hop | ✅ | ✔ | 1230/98 | 31371 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ✅ | ✔ | 8127/776 | 47964 | recall 1.00 |
| N01 | negative | ✅ | ✔ | 11212/412 | 41713 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 4093/137 | 24946 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1130/69 | 23861 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 4093/141 | 21793 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 4094/91 | 25516 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1131/62 | 21431 | refusal: judge-primary |
