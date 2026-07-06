# Baseline scorecard — `gpt-5.4-mini`

_Generated 2026-07-06T06:49:33.972155+00:00 · 24 tasks · ontology grounded in ALL runs._

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **25.0%** (6/24) |
| Tokens (total in/out) | 36440 / 3582 |
| Tokens (avg/task) | 1667.6 |
| Cost total (USD) | $0.016274 |
| Cost per correct answer (USD) | $0.002712 |
| Latency avg / p95 (ms) | 26566 / 55830 |
| Grounded (called Fabric IQ) | 100.0% |
| Multi-hop traversal correct | 0.0% |
| Frozen weights / single config | True / True |

> Cost pricing verified: **False** (source: placeholder - replace with your Foundry/AOAI pricing).

## Accuracy by category

| Category | Correct | Total | % |
| --- | --- | --- | --- |
| multi_hop | 0 | 10 | 0.0% |
| negative | 6 | 6 | 100.0% |
| single_hop | 0 | 8 | 0.0% |

## Per-task

| id | cat | correct | grounded | in/out tok | ms | detail |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | single_hop | ❌ | ✔ | 1510/141 | 24450 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ❌ | ✔ | 1508/145 | 19545 | expected 4.0 not found among numbers in answer |
| S03 | single_hop | ❌ | ✔ | 1476/101 | 10152 | recall 0.00, missing ['coastal_bay_lagoon', 'drinking_water_ |
| S04 | single_hop | ❌ | ✔ | 1586/171 | 31109 | expected 13.0 not found among numbers in answer |
| S05 | single_hop | ❌ | ✔ | 1509/137 | 16514 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ❌ | ✔ | 1527/156 | 21141 | expected 88.67 not found among numbers in answer |
| S07 | single_hop | ❌ | ✔ | 1511/133 | 23018 | expected 142.7 not found among numbers in answer |
| S08 | single_hop | ❌ | ✔ | 1517/144 | 23023 | expected 8.0 not found among numbers in answer |
| M01 | multi_hop | ❌ | ✔ | 1518/187 | 20350 | recall 0.00, missing ['Lake Champlain South Bay', 'Lake Roto |
| M02 | multi_hop | ❌ | ✔ | 1527/169 | 55830 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| M03 | multi_hop | ❌ | ✔ | 1510/136 | 26633 | recall 0.00, missing ['algaecide application (copper sulfate |
| M04 | multi_hop | ❌ | ✔ | 1527/170 | 50240 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| M05 | multi_hop | ❌ | ✔ | 1502/81 | 49952 | expected 10.0 not found among numbers in answer |
| M06 | multi_hop | ❌ | ✔ | 1523/144 | 20171 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ❌ | ✔ | 1522/177 | 22069 | recall 0.00, missing ['UV treatment', 'algaecide application |
| M08 | multi_hop | ❌ | ✔ | 1536/170 | 24110 | expected 185.67 not found among numbers in answer |
| M09 | multi_hop | ❌ | ✔ | 1526/173 | 21642 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ❌ | ✔ | 1537/147 | 56522 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| N01 | negative | ✅ | ✔ | 1519/160 | 30373 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 1523/173 | 17249 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1515/138 | 21832 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 1505/135 | 19695 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 1492/166 | 9205 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1514/128 | 22749 | refusal: judge-primary |
