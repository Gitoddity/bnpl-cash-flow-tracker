# Prompt 009 - Product Requirements Alignment

Date: 2026-06-09

## Full Prompt

```text
Review and update docs/product-requirements.md so it aligns with the approved MVP 1 Data Model, Calculation Rules, Test Cases, User Flows, and Success Criteria.

## Goal

This is a documentation-only alignment pass. Do not change the product vision, user problem, MVP objective, or MVP scope. Update terminology and requirements so they reflect the approved specifications.

## Change 1: Replace Obsolete Start Date Terminology

The approved data model no longer uses `start_date`.

Update all references to:

purchase_date
first_installment_date

### Required Capabilities

Current:

- Purchase amount
- Start date
- Installment count

Replace with:

- Purchase amount
- Currency
- Purchase date
- First installment date
- Installment count

### Example Scenario

Current:

Start date: 2026-06-07

Replace with:

Purchase Date: 2026-06-07
First Installment Date: 2026-06-07

## Change 2: Add Currency Support

The approved data model explicitly stores currency.

### Required Capabilities

Add:

- Currency

### Example Scenario

Add:

- Currency: CAD

## Change 3: Reflect Stable Internal Identifiers

The approved data model includes stable identifiers for:

credit_card_id
plan_id

Update Required Capabilities to acknowledge:

- Credit card identifier
- BNPL plan identifier

Do not over-emphasize implementation details; simply ensure the requirements are consistent with the approved model.

## Change 4: Align Aggregation Terminology

Current:

- Aggregated obligations by due date.
- Aggregated obligations by credit card.
- Aggregated obligations by month.

Replace with:

- Aggregated obligations by payment due date.
- Aggregated obligations by credit card.
- Derived cash-flow reporting by:
  - cash_flow_year
  - cash_flow_month
  - cash_flow_period

This must match the approved data model and calculation rules.

## Change 5: Add Installment Projection Reporting

The approved model includes `InstallmentProjection`.

Add a requirement that the engine must produce reporting output containing:

- Installment date
- Installment amount
- Credit card
- Statement cycle
- Payment due date
- Cash-flow period

Reference the InstallmentProjection concept without introducing UI requirements.

## Change 6: Add Validation Traceability

Under MVP Objective or Expected Value, add wording that:

The engine is considered validated when the approved scenarios documented in docs/test-cases.md pass successfully.

Clarify that the approved test cases are the authoritative business-rule validation source.

## Constraints

* Do not change product vision.
* Do not change user problem.
* Do not change MVP scope.
* Do not change approved business rules.
* Do not change approved test cases.
* Do not create implementation code.
* Do not create Python files.
* Do not create src/ or tests/ files.

## Prompt History

Add:

Prompt 009 - Product Requirements Alignment

Update prompts/prompt-registry.md:

Date: 2026-06-09
Purpose: align product requirements with approved MVP 1 specifications
Outcome: terminology, reporting, aggregation, identifiers, currency, and validation traceability aligned with approved documentation
Related documents:

  * docs/data-model.md
  * docs/calculation-rules.md
  * docs/test-cases.md
  * docs/user-flows.md
  * docs/success-criteria.md
Related prompts:

  * Prompt 002
  * Prompt 003
  * Prompt 004
  * Prompt 005
  * Prompt 007
  * Prompt 008

## Acceptance Criteria

* No references to `start_date` remain.
* Currency is included in requirements and examples.
* Stable identifiers are acknowledged.
* Aggregation terminology matches approved specifications.
* InstallmentProjection reporting is referenced.
* docs/test-cases.md is referenced as the authoritative validation source.
* No business rules change.
* No implementation files are created.
```
