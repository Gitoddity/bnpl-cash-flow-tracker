# Prompt Registry

This registry is the historical record of significant prompts that influence product, architecture, domain model, calculation rules, testing, or implementation decisions.

For every major prompt used during development:

- Save the prompt in the `prompts/` folder.
- Update this registry.
- Record the date.
- Record the prompt title.
- Record the purpose.
- Record the full prompt text or the file containing it.
- Record key outcomes.
- Record resulting decisions.
- Reference related documentation or implementation files that changed.

## Prompt 001 - Project Kickoff

Date: 2026-06-09

Purpose:

Establish the MVP 1 product vision, documentation set, calculation scope, architecture direction, testing expectations, and prompt management rules before any Python implementation begins.

Prompt:

Full prompt saved in `prompts/001-project-kickoff.md`.

Key Outcomes:

- Created documentation source-of-truth files for product requirements, data model, calculation rules, user flows, MVP scope, architecture, success criteria, and project instructions.
- Created the prompt management structure under `prompts/`.
- Established that documentation must be reviewed and approved before Python implementation starts.
- Established that the prompt registry is the source of truth for project decision history.

Decisions:

- MVP 1 will focus exclusively on a Python-based rules engine.
- MVP 1 will not include UI, database, API, cloud deployment, authentication, integrations, or AI features.
- Installment 1 occurs on the BNPL plan start date.
- Equal installment amounts are calculated as purchase amount divided by installment count.
- Money handling in implementation must be decimal-safe.
- A statement cycle includes charges after the previous statement end date through the current statement end date.
- An installment dated on the statement end day belongs to that closing statement.
- The payment due date is the configured due day following the statement close date.
- If the due day is earlier in the month than the statement end day, the due date falls in the following month.
- Aggregation groups obligations by due date, credit card, and calendar month of the due date.

Related Documentation:

- `docs/product-requirements.md`
- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/user-flows.md`
- `docs/mvp1-scope.md`
- `docs/architecture.md`
- `docs/success-criteria.md`
- `docs/project-instructions.md`
