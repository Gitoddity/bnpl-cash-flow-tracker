# Prompt 010 - MVP Scope Alignment

Date: 2026-06-09

## Full Prompt

```text
Review and update docs/mvp1-scope.md so it aligns with the approved MVP 1 Data Model, Calculation Rules, User Flows, Test Cases, Success Criteria, and Product Requirements.

## Summary

Update the existing MVP scope document at `docs/mvp1-scope.md` so it matches the approved data model, calculation rules, user flows, test cases, success criteria, and product requirements. This is a documentation-only terminology and traceability pass. The product objective, scope, and business rules remain unchanged.

## Key Changes
- Update supported inputs to match the approved model:
  - replace `Start date` with `Purchase date` and `First installment date`
  - add `Currency`
  - add `Credit card identifier`
  - add `BNPL plan identifier`

- Align aggregation scope with the approved calculation rules:
  - replace aggregation by month with aggregation by `payment due date`
  - keep aggregation by `credit card`
  - add derived cash-flow reporting fields:
    - `cash_flow_year`
    - `cash_flow_month`
    - `cash_flow_period`

- Add `InstallmentProjection` to expected outputs:
  - installment date
  - installment amount
  - credit card
  - statement cycle
  - payment due date
  - cash-flow period
  - use the `InstallmentProjection` concept without introducing UI requirements

- Update human-readable output wording to:
  - `Human-readable reporting output based on InstallmentProjection.`

- Strengthen the completion boundary:
  - replace generic example validation wording with
    - `The approved scenarios documented in docs/test-cases.md are validated successfully.`
  - add explicit traceability that `docs/test-cases.md` is the authoritative validation source for MVP 1 business-rule verification

## Prompt History
- Add `prompts/010-mvp-scope-alignment.md` containing the full prompt for this alignment pass.
- Update `prompts/prompt-registry.md` with Prompt 010:
  - Date: 2026-06-09
  - Purpose: align MVP scope with approved MVP 1 specifications
  - Outcome: terminology, reporting, aggregation, identifiers, currency, and validation traceability aligned with approved documentation
  - Related documents:
    - `docs/product-requirements.md`
    - `docs/data-model.md`
    - `docs/calculation-rules.md`
    - `docs/test-cases.md`
    - `docs/user-flows.md`
    - `docs/success-criteria.md`
  - Related prompts:
    - Prompt 002
    - Prompt 003
    - Prompt 004
    - Prompt 005
    - Prompt 007
    - Prompt 008
    - Prompt 009

## Assumptions
- The actual file to update is `docs/mvp1-scope.md` in this repository.
- This is documentation-only.
- No business rules change.
- No MVP scope expansion.
- No implementation files, Python files, `src/` files, or `tests/` files are created.
- `docs/test-cases.md` remains the authoritative validation source for approved scenarios.

## Acceptance Criteria

* No references to `start_date` remain.
* Currency is included in supported inputs.
* Stable identifiers are acknowledged.
* Aggregation terminology matches approved specifications.
* InstallmentProjection is explicitly in scope.
* Completion criteria reference `docs/test-cases.md`.
* No business rules change.
* No implementation files are created.
```
