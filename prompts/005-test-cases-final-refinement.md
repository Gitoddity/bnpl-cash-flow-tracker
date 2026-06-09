# Prompt 005 - Test Cases Final Refinement

Date: 2026-06-09

## Full Prompt

```text
Review the generated `docs/test-cases.md` and make two final refinements before the specification is considered complete.

## Change 1: Align TC-009 With Project Credit Card Settings

The current RBC example does not match the card settings used throughout the project.

Update TC-009:

Current:

RBC Mastercard
Statement End Day: 10
Payment Due Day: 25

Replace with:

RBC Mastercard
Statement End Day: 6
Payment Due Day: 27

Recalculate and update all affected expected values in TC-009:

* Statement cycle mapping
* Due date mapping
* Cash-flow periods
* Aggregated cash-flow obligations

The goal is to keep the test suite consistent with the project examples and real-world reference scenarios already documented elsewhere.

## Change 2: Strengthen TC-007 Rounding Validation

TC-007 already validates installment rounding.

Add an explicit validation section that confirms:

33.33 + 33.33 + 33.34 = 100.00

and

33.33 + 66.67 = 100.00

Add wording similar to:

Validation:

The sum of all generated installments must equal the original purchase amount exactly.

The sum of all aggregated cash-flow obligations must equal the original purchase amount exactly.

This test should explicitly protect against rounding-loss defects.

## Constraints

* Do not change any other test cases.
* Do not modify the approved data model.
* Do not modify the approved calculation rules.
* Do not introduce implementation code.
* Do not create Python files.
* Do not create `src/` or `tests/` directories.
* Keep all changes documentation-only.

## Prompt History

Record this refinement in prompt history according to project conventions.

Update the prompt registry and link this refinement to:

* Prompt 002 (Data Model Revision)
* Prompt 003 (Calculation Rules Clarification)
* Prompt 004 (Test Case Creation)

## Acceptance Criteria

* TC-009 uses:
  * RBC Statement End Day = 6
  * RBC Payment Due Day = 27
* All TC-009 expected outputs are recalculated correctly.
* TC-007 explicitly validates that totals reconcile exactly to the original purchase amount.
* No implementation files are created.
* No business rules are changed.
```
