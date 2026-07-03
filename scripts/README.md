# `scripts/` — Automation stubs (no runtime committed yet)

**Intent.** This directory will hold the automation used to provision, seed, bind, and operate the demo:
generating synthetic fixtures, loading OneLake sources, triggering the ontology **graph refresh**, and
running the agent / optimizer loops.

> **No runtime or language commitment is made in Phase 2.** The stubs below are intent placeholders only.
> The Python runtime version and the concrete implementation language for each script are **deferred to
> Phase 3/4** (see `PREREQUISITES.md` §4). Do not infer a language from the placeholder extensions.

**Status: stubs only.** Each stub documents *what* it will do, not *how*.

## Planned scripts (intent)
| Stub | Phase | Intent |
| --- | --- | --- |
| `generate_synthetic_data` | 3 | Produce the synthetic telemetry / lab / asset fixtures under `data/`. |
| `load_onelake_sources` | 4 | Create/populate the Eventhouse + Lakehouse managed tables in the workspace. |
| `refresh_ontology_graph` | 4 | Trigger the **manual graph refresh** after upstream data changes (verified-capabilities.md §1a). |
| `run_eval` | 6 | Run the eval suite (`azd ai agent eval run`) against the baseline / candidates. |
| `run_optimizer` | 6 | Run `azd ai agent optimize` (or the SkillOpt fallback if allow-listed access is unavailable, #10). |

See `docs/plan.md` for the full phase breakdown.
