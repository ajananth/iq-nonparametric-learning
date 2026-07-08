# Phase-6 optimization run — candidate ranking

_Generated 2026-07-08T06:48:38.373142+00:00 · model `gpt-5.4` (FROZEN) · reflection `gpt-5.4` · seed 1234 · mode LIVE._

**Winner: `c06`.** Objective = lexicographic (accuracy ↑, then tokens ↓). Adopt only if STRICTLY better on the held-out DEV split and the negative safe-refusal guardrail never regresses.

| cand | target | parent | TRAIN acc% | TRAIN tok | promising | DEV acc% | DEV tok | adopted |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| seed | seed | None | 91.67 | 64589 | True | 100.0 | 11462 | True |
| c01 | injection | seed | 100.0 | 145786 | True | 83.33 | 14431 | False |
| c02 | injection | seed | 100.0 | 52157 | True | 100.0 | 14686 | False |
| c03 | kb_params | seed | 100.0 | 146364 | True | 100.0 | 10228 | True |
| c04 | injection | c03 | 91.67 | 59710 | False | - | - | False |
| c05 | kb_params | c03 | 100.0 | 152100 | False | - | - | False |
| c06 | injection | c03 | 100.0 | 18752 | True | 100.0 | 8963 | True |
| c07 | injection | c06 | 66.67 | 17313 | False | - | - | False |
| c08 | kb_params | c06 | 83.33 | 18468 | False | - | - | False |
| c09 | injection | c06 | 100.0 | 19827 | False | - | - | False |
| c10 | injection | c06 | 91.67 | 23815 | False | - | - | False |

## Ranking by DEV objective (validated candidates)

1. `c06` (injection) — DEV acc 100.0%, 8963 tok — Trimming oversized row payloads is the safest remaining token-reduction lever: it preserves the verb
2. `c03` (kb_params) — DEV acc 100.0%, 10228 tok — A small retrieval-side nudge is the safest way to improve the missed multi-hop recall without changi
3. `seed` (seed) — DEV acc 100.0%, 11462 tok — Phase-5 baseline config.
4. `c02` (injection) — DEV acc 100.0%, 14686 tok — Remove the synthesized answer so the model relies only on verbatim ontology rows. This directly addr
5. `c01` (injection) — DEV acc 83.33%, 14431 tok — The current setting injects a synthesized answer alongside raw rows. That extra text can bias the mo
