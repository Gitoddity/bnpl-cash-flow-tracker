# Prompt 003 - Calculation Rules Aggregation Clarification

Date: 2026-06-09

## Full Prompt

```text
Review and update `docs/calculation-rules.md`.

The document is already largely correct and aligned with the revised data model. Make only the following refinements.

## Change 1: Simplify Cash Flow Aggregation Keys

Current wording:

The engine must aggregate obligations by:

* Due date.
* Credit card.
* Cash-flow year-month.

Replace with:

The engine must aggregate obligations by:

* Credit card.
* Payment due date.

Add the following clarification:

* `cash_flow_year`, `cash_flow_month`, and `cash_flow_period` are derived from the payment due date.
* `cash_flow_period` uses the year-month of the payment due date.

Rationale:

The due date already determines the year, month, and cash-flow period, so listing both as aggregation keys is redundant.

## Change 2: Add Additional Edge Case

In the "Edge Cases To Test" section, add:

* Purchase amount that does not divide evenly across installments.

This edge case validates the rounding rule and remainder assignment logic.

## Constraints

* Do not change any other calculation behavior.
* Do not modify examples unless required.
* Do not introduce implementation code.
* Do not create Python files, tests, or source files.
* Preserve the existing structure and intent of the document.

## Documentation Updates

Because this is a rules clarification:

* Update prompt history and registry documentation according to project conventions.
* Record the reason for the change and the decision made.
* Link the update to the data model revision completed on 2026-06-09.

## Acceptance Criteria

* Aggregation keys are based only on credit card and payment due date.
* Cash-flow period is explicitly documented as derived from payment due date.
* Rounding edge-case coverage is included in testing.
* No behavioral changes beyond the requested clarification.
```
