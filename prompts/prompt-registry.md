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

## Prompt 002 - Data Model Review

Date: 2026-06-09

Purpose:

Improve the conceptual data model before Python implementation, focusing on stable identifiers, explicit money/date/frequency fields, calculation clarity, and future dataclass implementation.

Prompt:

Full prompt saved in `prompts/002-data-model-review.md`.

Key Outcomes:

- Added stable internal IDs for credit cards and BNPL plans.
- Updated installments to reference `plan_id` and `credit_card_id`.
- Added explicit currency handling with MVP 1 default `CAD`.
- Replaced active `start_date` terminology with `purchase_date` and `first_installment_date`.
- Defined explicit installment frequency values, with `BIWEEKLY` supported in MVP 1.
- Clarified statement cycle inclusion and credit card due date rules.
- Expanded cash-flow obligation period fields.
- Added explicit installment rounding behavior.
- Added a non-persistent `InstallmentProjection` model for reporting.
- Added Python implementation notes for dataclasses, `Decimal`, dates, enums/constants, and pure functions.

Decisions:

- `first_installment_date` replaces `start_date` in current active docs and examples.
- Historical prompt files are not retroactively edited.
- IDs are stable internal application identifiers, not database primary keys.
- The due date is calculated as the first occurrence of `payment_due_day` after the statement cycle close date.
- Cash-flow aggregation uses due date, credit card, and cash-flow year-month.

Related Documentation:

- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/user-flows.md`
- `docs/success-criteria.md`
- `docs/project-instructions.md`

## Prompt 003 - Calculation Rules Aggregation Clarification

Date: 2026-06-09

Purpose:

Clarify cash-flow aggregation keys and add explicit testing coverage for purchase amounts that do not divide evenly across installments.

Prompt:

Full prompt saved in `prompts/003-calculation-rules-aggregation-clarification.md`.

Key Outcomes:

- Simplified cash-flow aggregation keys to credit card and payment due date.
- Documented that `cash_flow_year`, `cash_flow_month`, and `cash_flow_period` are derived from payment due date.
- Added uneven purchase amount division to calculation edge cases.
- Linked the clarification to the Prompt 002 data model revision completed on 2026-06-09.

Decisions:

- Cash-flow year, month, and period are not independent aggregation keys because payment due date already determines them.
- `cash_flow_period` remains a derived `YYYY-MM` reporting field based on payment due date.
- No calculation behavior changed beyond clarifying aggregation terminology and edge-case coverage.

Related Documentation:

- `docs/calculation-rules.md`
- `docs/data-model.md`

## Prompt 004 - MVP 1 Test Cases

Date: 2026-06-09

Purpose:

Define MVP 1 business-rule test cases before implementation, using the approved data model and calculation rules as the source of truth.

Prompt:

Full prompt saved in `prompts/004-test-cases.md`.

Key Outcomes:

- Created `docs/test-cases.md` with 11 business-rule test cases.
- Covered standard Klarna Pay in 4, statement boundary dates, due-date month behavior, uneven installment rounding, multiple plans, multiple cards, year rollover, and leap-year handling.
- Added explicit leap-year installment dates including `2028-02-29`.
- Documented expected installment schedules, statement cycles, due dates, cash-flow periods, and aggregated obligations.

Decisions:

- Test cases follow the approved data model and calculation rules.
- Cash-flow obligations in test cases aggregate by credit card and payment due date.
- TC-011 validates leap-day handling through installment generation, statement mapping, due-date mapping, cash-flow period derivation, and aggregation.
- No implementation code, Python files, `src/` files, or `tests/` files were created.

Related Documentation:

- `docs/test-cases.md`

## Prompt 005 - Test Cases Final Refinement

Date: 2026-06-09

Purpose:

Finalize test-case documentation consistency before implementation by aligning TC-009 with approved RBC Mastercard settings and strengthening TC-007 rounding reconciliation checks.

Prompt:

Full prompt saved in `prompts/005-test-cases-final-refinement.md`.

Key Outcomes:

- Updated TC-009 to use RBC Mastercard Statement End Day `6` and Payment Due Day `27`.
- Recalculated TC-009 RBC statement cycle, due date, cash-flow period, and aggregated obligation.
- Added explicit TC-007 validation that installment totals and aggregated cash-flow totals reconcile exactly to the original purchase amount.

Decisions:

- TC-009 uses the project-approved RBC Mastercard settings.
- TC-007 explicitly protects against rounding-loss defects.
- No business rules changed; this was a test-spec refinement only.

Related Documentation:

- `docs/test-cases.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases

## Prompt 007 - User Flows Workflow Entry Point Update

Date: 2026-06-09

Purpose:

Improve end-to-end workflow clarity by adding a calculation-run entry point before credit card and BNPL plan definition flows.

Prompt:

Full prompt saved in `prompts/007-user-flows-alignment.md`.

Key Outcomes:

- Added a `Flow 0` calculation-run entry point to `docs/user-flows.md`.
- Updated user-flow terminology to reflect stable IDs, explicit currency, and `cash_flow_period`.
- Documented the `InstallmentProjection` reporting flow.
- Renumbered the real-world validation flow to remain the final flow.

Decisions:

- The user-flow specification starts with the calculation run entry point before configuration flows.
- `InstallmentProjection` is part of the documented reporting flow, not a business-rule change.
- No approved business rules changed.

Related Documentation:

- `docs/user-flows.md`
- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/test-cases.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases
- Prompt 005 - Test Cases Final Refinement

## Prompt 008 - Success Criteria Alignment

Date: 2026-06-09

Purpose:

Align success criteria with approved MVP 1 specifications.

Prompt:

Full prompt saved in `prompts/008-success-criteria-alignment.md`.

Key Outcomes:

- Updated success criteria to use approved aggregation terminology.
- Added traceability to `docs/test-cases.md`.
- Aligned reporting language with `InstallmentProjection`.
- Strengthened real-world validation traceability.

Decisions:

- Success criteria reference `docs/test-cases.md` as the authoritative validation source for real-world example verification.
- Reporting criteria are expressed in terms of `InstallmentProjection`.
- No business rules changed.

Related Documentation:

- `docs/success-criteria.md`
- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/test-cases.md`
- `docs/user-flows.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases
- Prompt 005 - Test Cases Final Refinement
- Prompt 007 - User Flows Workflow Entry Point Update

## Prompt 009 - Product Requirements Alignment

Date: 2026-06-09

Purpose:

Align product requirements with approved MVP 1 specifications.

Prompt:

Full prompt saved in `prompts/009-product-requirements-alignment.md`.

Key Outcomes:

- Updated product requirements terminology to match the approved data model.
- Added currency, stable identifier, and `InstallmentProjection` reporting references.
- Added validation traceability to `docs/test-cases.md`.

Decisions:

- Product requirements reference `docs/test-cases.md` as the authoritative validation source for approved scenarios.
- Reporting requirements are expressed in terms of `InstallmentProjection`.
- No business rules changed.

Related Documentation:

- `docs/product-requirements.md`
- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/test-cases.md`
- `docs/user-flows.md`
- `docs/success-criteria.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases
- Prompt 005 - Test Cases Final Refinement
- Prompt 007 - User Flows Workflow Entry Point Update
- Prompt 008 - Success Criteria Alignment

## Prompt 010 - MVP Scope Alignment

Date: 2026-06-09

Purpose:

Align MVP scope with approved MVP 1 specifications.

Prompt:

Full prompt saved in `prompts/010-mvp-scope-alignment.md`.

Key Outcomes:

- Updated MVP scope terminology to match the approved data model.
- Added reporting and aggregation references aligned with approved calculation rules.
- Added validation traceability to `docs/test-cases.md`.

Decisions:

- MVP scope references `docs/test-cases.md` as the authoritative validation source for approved scenarios.
- Reporting requirements are expressed in terms of `InstallmentProjection`.
- No business rules changed.

Related Documentation:

- `docs/product-requirements.md`
- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/test-cases.md`
- `docs/user-flows.md`
- `docs/success-criteria.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases
- Prompt 005 - Test Cases Final Refinement
- Prompt 007 - User Flows Workflow Entry Point Update
- Prompt 008 - Success Criteria Alignment
- Prompt 009 - Product Requirements Alignment

## Prompt 012 - Architecture Alignment

Date: 2026-06-09

Purpose:

Align architecture with approved MVP 1 specifications.

Prompt:

Full prompt saved in `prompts/012-architecture-alignment.md`.

Key Outcomes:

- Updated architecture terminology to match the approved data model.
- Clarified reporting ownership for `InstallmentProjection`.
- Added validation traceability to `docs/test-cases.md`.

Decisions:

- `InstallmentProjection` belongs to the Reporting Layer.
- `docs/test-cases.md` is the authoritative source for business-rule validation scenarios.
- No business rules changed.

Related Documentation:

- `docs/data-model.md`
- `docs/calculation-rules.md`
- `docs/test-cases.md`
- `docs/user-flows.md`
- `docs/success-criteria.md`
- `docs/product-requirements.md`
- `docs/mvp1-scope.md`

Related Prompts:

- Prompt 002 - Data Model Review
- Prompt 003 - Calculation Rules Aggregation Clarification
- Prompt 004 - MVP 1 Test Cases
- Prompt 005 - Test Cases Final Refinement
- Prompt 007 - User Flows Workflow Entry Point Update
- Prompt 008 - Success Criteria Alignment
- Prompt 009 - Product Requirements Alignment
- Prompt 010 - MVP Scope Alignment
- Prompt 011 - MVP Scope Final Alignment

## Prompt 013 - MVP 2 Phase 6 Final Verification

Date: 2026-06-17

Purpose:

Finalize MVP 2 documentation alignment and verify the completed MVP 2 workflow without changing product scope or calculation behavior.

Prompt:

Full prompt saved in `prompts/013-mvp2-phase6-final-verification.md`.

Key Outcomes:

- Confirmed that the implemented MVP 2 workflow matches the documented local JSON-driven architecture.
- Confirmed that no scope change was required in the MVP 2 docs during the final verification pass.
- Recorded the final verification phase in the project prompt registry.

Decisions:

- No documentation updates were required beyond the prompt-registry record for final verification.
- MVP 2 remains local, JSON-driven, and CLI-based.
- MVP 1 calculation rules remain untouched.

Related Documentation:

- `docs/mvp2-scope.md`
- `docs/json-contract.md`
- `docs/mvp2-architecture.md`
- `docs/mvp2-implementation-plan.md`

Related Prompts:

- Prompt 013 - MVP 2 Phase 6 Final Verification
