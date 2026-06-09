# Prompt 012 - Architecture Alignment

Date: 2026-06-09

## Full Prompt

```text
Review and update docs/architecture.md so it aligns with the approved MVP 1 Data Model, Calculation Rules, Test Cases, User Flows, Success Criteria, Product Requirements, and MVP Scope.

## Summary

Update docs/architecture.md so it aligns with the approved MVP 1 Data Model, Calculation Rules, Test Cases, User Flows, Success Criteria, Product Requirements, and MVP Scope.

This is a documentation-only alignment pass. No architecture scope expansion, business-rule changes, or implementation files are being created.

## Key Changes

### Update Rules Layer Aggregation Terminology

Current wording:

`- Aggregate obligations by due date, credit card, and month.`

Replace with:

`- Aggregate obligations by payment due date and credit card.`
`- Derive cash-flow reporting fields:`
  - `cash_flow_year`
  - `cash_flow_month`
  - `cash_flow_period`

Clarify that:

* Payment due date and credit card are aggregation keys.
* `cash_flow_year`, `cash_flow_month`, and `cash_flow_period` are derived reporting fields.

### Align Domain Layer With Approved Data Model

Update Domain Layer responsibilities to include all approved domain concepts:

* Credit card model
* BNPL plan model
* Installment model
* Statement cycle model
* Due date model
* Cash flow obligation model

Add clarification:

`InstallmentProjection is not a source-of-truth domain entity.`

It is a reporting-oriented projection model defined in the approved data model.

### Clarify InstallmentProjection Ownership

Choose one architectural ownership model and document it explicitly:

Preferred approach:

`InstallmentProjection belongs to the Reporting Layer.`

Reporting responsibilities should include:

* Build InstallmentProjection objects from calculation results.
* Render InstallmentProjection output.
* Render aggregated cash-flow summaries.

Clarify that business rules remain in the Rules Layer.

### Align Tests With Approved Validation Source

Update the Tests section to state:

`docs/test-cases.md is the authoritative source for business-rule validation scenarios.`

Add guidance that:

* Unit tests should validate individual rule behavior.
* Scenario tests should implement the approved test cases documented in `docs/test-cases.md`.

### Update Recommended Project Structure

If InstallmentProjection is assigned to the Reporting Layer, keep the current structure:

`reporting/`

and clarify that reporting models may reside there.

Do not introduce unnecessary layers or folders.

## Prompt History

* Add `prompts/012-architecture-alignment.md` containing the full prompt for this alignment pass.
* Update `prompts/prompt-registry.md` with Prompt 012:

  * Date: 2026-06-09
  * Purpose: align architecture with approved MVP 1 specifications
  * Outcome: architecture terminology, aggregation behavior, reporting responsibilities, and validation traceability aligned with approved documentation
  * Related documents:

    * `docs/data-model.md`
    * `docs/calculation-rules.md`
    * `docs/test-cases.md`
    * `docs/user-flows.md`
    * `docs/success-criteria.md`
    * `docs/product-requirements.md`
    * `docs/mvp1-scope.md`
  * Related prompts:

    * Prompt 002
    * Prompt 003
    * Prompt 004
    * Prompt 005
    * Prompt 007
    * Prompt 008
    * Prompt 009
    * Prompt 010
    * Prompt 011

## Assumptions

* This is documentation-only.
* No business rules change.
* No architecture scope expansion.
* No implementation files, Python files, `src/` files, or `tests/` files are created.
* `docs/test-cases.md` remains the authoritative validation source for business-rule verification.

## Acceptance Criteria

* Aggregation terminology matches approved specifications.
* InstallmentProjection ownership is explicitly documented.
* Domain and Reporting responsibilities are clearly separated.
* Architecture references `docs/test-cases.md` as the validation source.
* No business rules change.
* No implementation files are created.
```
