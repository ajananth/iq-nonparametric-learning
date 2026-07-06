# Baseline scorecard — `gpt-5.4`

_Generated 2026-07-06T06:37:54.001535+00:00 · 24 tasks · ontology grounded in ALL runs._

## Headline metrics

| Metric | Value |
| --- | --- |
| Accuracy (overall) | **29.2%** (7/24) |
| Tokens (total in/out) | 36168 / 3625 |
| Tokens (avg/task) | 1658.0 |
| Cost total (USD) | $0.08146 |
| Cost per correct answer (USD) | $0.011637 |
| Latency avg / p95 (ms) | 27361 / 44472 |
| Grounded (called Fabric IQ) | 100.0% |
| Multi-hop traversal correct | 0.0% |
| Frozen weights / single config | True / True |

> Cost pricing verified: **False** (source: placeholder - replace with your Foundry/AOAI pricing).

## Accuracy by category

| Category | Correct | Total | % |
| --- | --- | --- | --- |
| multi_hop | 0 | 10 | 0.0% |
| negative | 6 | 6 | 100.0% |
| single_hop | 1 | 8 | 12.5% |

## Per-task

| id | cat | correct | grounded | in/out tok | ms | detail |
| --- | --- | --- | --- | --- | --- | --- |
| S01 | single_hop | ❌ | ✔ | 1496/72 | 42002 | expected 20.0 not found among numbers in answer |
| S02 | single_hop | ✅ | ✔ | 1501/78 | 22737 | found 4.0 within tol of 4.0 |
| S03 | single_hop | ❌ | ✔ | 1498/82 | 23952 | recall 0.43, missing ['coastal_bay_lagoon', 'drinking_water_ |
| S04 | single_hop | ❌ | ✔ | 1500/77 | 22855 | expected 13.0 not found among numbers in answer |
| S05 | single_hop | ❌ | ✔ | 1510/151 | 24480 | substring match for 'Cyanobacteria' |
| S06 | single_hop | ❌ | ✔ | 1523/123 | 22519 | expected 88.67 not found among numbers in answer |
| S07 | single_hop | ❌ | ✔ | 1500/77 | 20056 | expected 142.7 not found among numbers in answer |
| S08 | single_hop | ❌ | ✔ | 1508/105 | 23011 | expected 8.0 not found among numbers in answer |
| M01 | multi_hop | ❌ | ✔ | 1523/227 | 25450 | recall 0.00, missing ['Lake Champlain South Bay', 'Lake Roto |
| M02 | multi_hop | ❌ | ✔ | 1529/288 | 44472 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| M03 | multi_hop | ❌ | ✔ | 1503/127 | 29968 | recall 0.00, missing ['algaecide application (copper sulfate |
| M04 | multi_hop | ❌ | ✔ | 1530/214 | 41053 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| M05 | multi_hop | ❌ | ✔ | 1507/115 | 23583 | expected 10.0 not found among numbers in answer |
| M06 | multi_hop | ❌ | ✔ | 1529/191 | 26143 | recall 0.00, missing ['Alexandrium minutum', 'Chaetoceros mu |
| M07 | multi_hop | ❌ | ✔ | 1506/139 | 25996 | recall 0.00, missing ['UV treatment', 'algaecide application |
| M08 | multi_hop | ❌ | ✔ | 1534/141 | 24898 | expected 185.67 not found among numbers in answer |
| M09 | multi_hop | ❌ | ✔ | 1514/168 | 22438 | substring match for 'Spirogyra spp.' |
| M10 | multi_hop | ❌ | ✔ | 1531/229 | 59716 | recall 0.00, missing ['Blue Lake Reservoir', 'Chesapeake Bay |
| N01 | negative | ✅ | ✔ | 1500/188 | 26327 | refusal: judge-primary |
| N02 | negative | ✅ | ✔ | 1515/218 | 25685 | refusal: judge-primary |
| N03 | negative | ✅ | ✔ | 1397/135 | 6490 | refusal: judge-primary |
| N04 | negative | ✅ | ✔ | 1502/179 | 26069 | refusal: judge-primary |
| N05 | negative | ✅ | ✔ | 1499/158 | 24669 | refusal: judge-primary |
| N06 | negative | ✅ | ✔ | 1513/143 | 22092 | refusal: judge-primary |
