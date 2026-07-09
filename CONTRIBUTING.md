# Contributing

Thanks for contributing to **IQ Non-Parametric Learning**. This project is governed by
[`CONSTITUTION.md`](./CONSTITUTION.md) — please read it first. The rules there **win** over any convenience.

## The one hard workflow rule: Epic → Issue → PR (Art. XIII)

**No change is executed — no matter how small — unless it is backed by the full chain:**

1. a high-level **GitHub Epic**,
2. a specific **GitHub Issue** linked to that epic, and
3. a **Pull Request** linked to that issue that delivers the change.

This chain is verified **before** any work starts, every time. Merges happen only via **reviewed PRs**;
direct pushes to `main` are not allowed.

### Steps
1. **Find or open the Epic.** Use the **Epic** issue template.
2. **Open a Task issue** under that epic. Use the **Task** issue template; reference the parent epic.
3. **Branch** off up-to-date `main` (e.g. `phaseN/short-description`).
4. **Commit** in small, auditable increments (Art. IX). Include the co-author trailer:

   ```
   Co-authored-by: Copilot App <223556219+Copilot@users.noreply.github.com>
   ```
5. **Open a PR** using the PR template. The body must link the **Epic** and the **Issue**
   (`Closes #<n>`) and complete the **constitution-compliance checklist**.
6. **Do not self-merge.** PRs are merged only after review by a code owner (see `.github/CODEOWNERS`).

## Non-negotiables to keep in mind
- **Accuracy (Art. I):** every technical claim about Microsoft products/APIs is verified against a **primary
  source** and cited. `docs/verified-capabilities.md` is the single source of truth; cite it, don't
  contradict it. State preview/GA status. If you can't verify something, say so and document a fallback.
- **Secrets (Art. VI):** never commit secrets, keys, endpoints, or tenant/client IDs. Use `.env.example`
  placeholders only; real values go in a local, git-ignored `.env`.
- **Non-parametric integrity (Art. II) & model independence (Art. III):** optimize text/config only; never
  fine-tune weights; no model-specific hardcoding.
- **Reproducibility (Art. V):** commit **synthetic** data only; real data is wired via config and never
  committed.
- **Public safety (Art. VII/VIII):** nothing is made public without explicit approval; the repo stays
  **private** until the publication gate.

## License

Per Constitution Art. VII.3: **code is MIT** (see [`LICENSE`](./LICENSE)); **prose / documentation /
article content is CC-BY**. By contributing you agree your contributions are licensed on the same terms.
