# Prompt 004 - MVP 1 Test Cases

Date: 2026-06-09

## Full Prompt

```text
Create `docs/test-cases.md` for the BNPL Cash Flow Tracker MVP 1.

Goal:
Define clear business-rule test cases before implementation begins. These test cases should validate the approved data model and calculation rules.

Use the existing documentation as source of truth:

* `docs/data-model.md`
* `docs/calculation-rules.md`

## Required Test Case Format

Each test case should use this structure:

## TC-001 Test Case Name

Purpose:
...

Input:
...

Expected Installments:
...

Expected Statement Cycle Mapping:
...

Expected Due Date Mapping:
...

Expected Cash Flow Obligations:
...

## Required Test Cases

Create test cases for:

1. Standard Klarna Pay in 4 using Tangerine Mastercard.
2. Installment before statement end day.
3. Installment exactly on statement end day.
4. Installment after statement end day.
5. Due date in the same calendar month as statement close.
6. Due date in the following calendar month.
7. Purchase amount that does not divide evenly across installments.
8. Multiple BNPL plans assigned to the same card and same due date.
9. Multiple cards with different statement and due days.
10. December to January year rollover.
11. Leap year handling.

## Rules To Validate

The test cases must validate:

* Installment 1 occurs on `first_installment_date`.
* BIWEEKLY installments occur every 14 days.
* Installment amounts use decimal-safe rounding.
* Any rounding remainder is assigned to the final installment.
* Statement cycle rule:
  `previous_cycle_end_date < charge_date <= cycle_end_date`
* Installments on statement end day belong to that closing statement.
* Payment due date is the first occurrence of `payment_due_day` after statement close.
* Cash flow obligations aggregate by credit card and payment due date.
* `cash_flow_period` is derived from payment due date using `YYYY-MM`.

## Constraints

* Documentation only.
* Do not create Python files.
* Do not create `src/` or `tests/` files.
* Do not introduce implementation code.
* Do not change existing data model or calculation rules unless a clear contradiction is found.
* Keep the document readable enough that a developer can later translate each case into automated tests.
* Use simple realistic amounts and dates.
* Prefer CAD examples.

## Prompt History

Also update the project prompt history according to existing project conventions:

* Add a new prompt file for this test-case creation.
* Update `prompts/prompt-registry.md`.
* Link this test-case work to the approved data model and calculation rules revisions from 2026-06-09.

## Acceptance Criteria

* `docs/test-cases.md` exists.
* It includes all required test cases.
* Each test case has clear inputs and expected outputs.
* Expected outputs include installment dates, statement cycles, due dates, and aggregated cash-flow obligations where applicable.
* Rounding, boundary dates, multiple plans, multiple cards, year rollover, and leap year behavior are explicitly covered.
* No implementation files are created.
```

## Leap-Year Refinement Prompt

```text
Review the approved Test Cases Documentation Plan before execution and make one additional refinement.

## Leap Year Test Case Enhancement

Update `TC-011 Leap Year Handling` so that it contains explicit expected installment dates rather than only a narrative description.

The purpose is to verify:

* February 29, 2028 is treated as a valid calendar date.
* BIWEEKLY installment generation correctly uses 14-day date arithmetic.
* Installment schedules remain correct when crossing a leap day.
* Statement-cycle mapping, due-date mapping, and cash-flow aggregation continue to work correctly around February 29.

Use explicit installment dates that include leap day.

Example pattern:

First Installment Date: 2028-02-15

Expected Installments:

1. 2028-02-15
2. 2028-02-29
3. 2028-03-14
4. 2028-03-28

The final test case should also include:

* Expected statement-cycle assignments.
* Expected payment due dates.
* Expected cash-flow periods.
* Expected aggregated cash-flow obligations.

## Constraints

* Do not change any other approved test cases.
* Do not change the approved data model.
* Do not change the approved calculation rules.
* Do not create implementation code.
* Do not create Python files, `src/` files, or `tests/` files.
* Keep the change limited to strengthening leap-year coverage.

## Acceptance Criteria

* TC-011 contains explicit expected installment dates.
* At least one installment date is `2028-02-29`.
* Leap-day handling is validated through the entire calculation chain:
  installment generation -> statement cycle mapping -> due date mapping -> cash-flow aggregation.
```
