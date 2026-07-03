# Constitution — IQ Non-Parametric Learning Initiative

> This is the governing document for the project. Every plan, article draft, code change, and
> decision **must** comply with these rules. When any rule conflicts with a request, the rule wins
> until the user explicitly amends this constitution.

## Purpose
Deliver a **public article + runnable GitHub repo** showing how the **Microsoft IQ stack**
(Fabric IQ Ontology + Foundry) supplies enterprise context, combined with **non-parametric learning**
(frozen model weights; optimize harness/prompts/tools) — proving two headline values:
**the Fabric IQ ↔ Foundry semantic contract** and **frontier model swappability**.

---

## Article I — Accuracy & Verification (non-negotiable)
1. The source material (Gemini-generated PDF) is treated as **unverified** until confirmed.
2. **No technical claim** about Microsoft products, APIs, CLIs, SDKs, or feature availability enters
   the article or repo until validated against **official primary sources** (Microsoft Learn,
   official GitHub repos, product blogs). LLM/search summaries are leads, not proof.
3. Every non-obvious factual claim in the article carries an inline **citation** to a primary source.
4. Preview/GA status of every feature is stated explicitly and dated.
5. If a claimed capability cannot be verified, we say so and provide a documented fallback — we never
   present speculation as fact.

## Article II — Non-Parametric Integrity
1. The demo **never** fine-tunes or alters model weights. Optimization happens strictly in text space
   (instructions, tools, skills, model selection, reasoning effort).
2. Any change that would require weight updates is out of scope and must be flagged, not implemented.

## Article III — Model Independence
1. Business logic and data semantics must contain **zero model-specific hardcoding**.
2. The model is a swappable commodity behind config; swapping it must require **no code rewrites**.
3. The model-swappability story must remain demonstrable end-to-end at all times.

## Article IV — Separation of Concerns
1. Data structure and business vocabulary live in the **Fabric IQ ontology**, never baked into prompts.
2. The agent queries semantics via natural language / the ontology tool — no raw SQL/schema coupling
   in the harness.

## Article V — Reproducibility
1. Everything in the repo must be runnable by an independent third party.
2. Ship **synthetic fixtures**; the demo must run without any private/real data.
3. Real customer data is wired via config only and is **never** committed.

## Article VI — Security & Secrets
1. No secrets, connection strings, tenant/client IDs, endpoints, or keys in the repo — ever.
2. All such values come from environment variables / config templates (e.g. `.env.example`).
3. Least-privilege everywhere (e.g. scoped Entra permissions, documented and minimal).

## Article VII — Public-Content Safety
1. No confidential, internal-only, or customer-identifying information in article or repo.
2. Respect Microsoft trademarks/branding; correctly attribute Microsoft Research work (e.g. SkillOpt).
3. Code license: MIT. Prose license: CC-BY (unless user chooses otherwise).

## Article VIII — Human-in-the-Loop Gates
1. **Nothing is published, pushed to a public remote, or made irreversible without explicit user
   approval** for that specific action.
2. Naming the public repo, first public push, and article publication are each explicit approval gates.

## Article IX — Plan & Traceability
1. `plan.md` + the session todo database are the **single source of truth** for scope and progress.
2. Plan and todos are updated at every milestone; work maps back to a todo.
3. Progress moves in **small, auditable increments** with clear commit/checkpoint boundaries.

## Article X — Ways of Working
1. Work happens in the dedicated **IQ Non-Parametric Learning** session/workspace, not scattered chats.
2. Phase 0 (validate tooling) **gates** all build work.
3. Decisions and their rationale are recorded (in plan.md or ADR-style notes under `docs/`).
4. This constitution is reviewed at the start of each major phase and amended only with user consent;
   amendments are dated.

## Article XI — Master / Child Session Orchestration
1. A single **master (orchestrator) session** owns the plan, the constitution, and coordination.
2. Discrete workstreams are delegated to **child sessions** (as done for Research IQ); the master
   spawns, steers, and integrates them.
3. Every child session must read and comply with this constitution before doing any work.
4. The master keeps `plan.md` and the todo DB authoritative across all child sessions.

## Article XII — Plan-Before-Implement (hard gate)
1. **Every activity is thoroughly planned before any implementation.**
2. **No implementation begins in any session until the user has explicitly approved that plan.**
3. This applies to child sessions too: they plan, get master/user approval, then execute.

## Article XIII — GitHub Traceability (Epic → Issue → PR)
1. **No change is executed — no matter how small — unless it is backed by:**
   a. a high-level **GitHub Epic**,
   b. a specific **GitHub Issue** linked to that epic, and
   c. a **Pull Request** linked to that issue that delivers the change.
2. This chain (Epic → Issue → PR) is verified **before executing any task in any session, every time**.
3. Work is merged only via reviewed PRs; direct pushes to the default branch are not allowed.
4. A GitHub repo (initially **private**) is created to host these epics/issues/PRs; it is made
   **public only at the publication approval gate** (Article VIII).

---

## Amendment log
- (initial) — Constitution established.
