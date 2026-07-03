<!--
Constitution Art. XIII: every PR links to its Issue (and via that, its Epic). Fill in the links and the
compliance checklist below. See CONSTITUTION.md and CONTRIBUTING.md.
-->

## Summary
<!-- What does this PR change and why? -->

## Traceability (Art. XIII)
- **Epic:** <!-- e.g. EPIC A (#1) -->
- **Closes:** <!-- e.g. Closes #15 -->

## Constitution compliance checklist
- [ ] **Art. I — Accuracy:** every technical claim is backed by a primary source and cites
      `docs/verified-capabilities.md` (or a new primary-source citation is added). Preview/GA status stated.
- [ ] **Art. II — Non-parametric integrity:** no model weights are altered; changes are text/config only.
- [ ] **Art. III — Model independence:** no model-specific hardcoding; the model stays swappable via config.
- [ ] **Art. IV — Separation of concerns:** schema/vocabulary stays in the ontology, not baked into prompts.
- [ ] **Art. V — Reproducibility:** only synthetic fixtures committed; no real/customer data.
- [ ] **Art. VI — Secrets:** no secrets/keys/endpoints/tenant or client IDs committed; only `.env.example`
      placeholders. `.gitignore` still covers `.env`, `*.key`, `*.pem`, `secrets/`.
- [ ] **Art. VII — Public-content safety:** no confidential/customer-identifying info; correct attribution.
- [ ] **Art. VIII — Human-in-the-loop:** nothing published/made public without explicit approval; **PR not
      self-merged**.
- [ ] **Art. IX/XII — Plan & traceability:** work maps to an approved plan/todo and to the linked Issue.

## Notes for reviewer
<!-- Anything that could not be verified (flag it), open discrepancies, or follow-ups. -->
