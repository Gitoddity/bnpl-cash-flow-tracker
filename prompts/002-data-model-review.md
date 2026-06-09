# Prompt 002 - Data Model Review

Date: 2026-06-09

## Full Prompt

```text
Review and update the BNPL Cash Flow Tracker MVP 1 data model.

Goal:
Improve the existing conceptual data model before implementation, focusing on correctness, clarity, and future Python dataclass implementation.

Please review the current markdown data model and update it with the following changes:

1. Add stable IDs
- Add an internal `id` field to Credit Card.
- Add an internal `id` field to BNPL Plan.
- Installments should reference `plan_id` and `credit_card_id`, not rely only on names.

2. Add currency
- Add `currency` to BNPL Plan.
- MVP 1 may assume CAD, but the model should explicitly store it.

3. Split purchase date from first installment date
- Replace or clarify `start_date`.
- Add:
  - `purchase_date`
  - `first_installment_date`
- For MVP 1, these may be the same date, but the model should not assume that forever.

4. Improve installment frequency
- Replace vague frequency handling with an explicit frequency concept.
- MVP 1 supports BIWEEKLY / every 14 days.
- The model should be ready to later support WEEKLY and MONTHLY.

5. Clarify statement cycle rule
- Define the cycle inclusion rule explicitly as:
  previous_cycle_end_date < charge_date <= cycle_end_date
- Confirm that a charge on the statement end day belongs to that closing statement.

6. Clarify credit card due date rule
- Define the due date as the first occurrence of `payment_due_day` after the statement cycle close date.
- Do not rely only on comparing due day and statement end day.

7. Improve cash flow obligation model
- Add `statement_cycle_end_date`.
- Add explicit year/month handling.
- Do not use only `month`.
- Prefer:
  - `cash_flow_year`
  - `cash_flow_month`
  - `cash_flow_period`
- Define `cash_flow_period` as the calendar year-month of the credit card payment due date, such as `2026-07`.

8. Update aggregation keys
Cash Flow Obligation should aggregate by:
- due date
- credit card
- cash flow year-month

9. Define money rounding
- Use decimal-safe money handling.
- Binary floating point must not be used.
- Add an explicit installment rounding rule:
  - Divide purchase amount across installments.
  - Round to 2 decimal places.
  - Assign any remainder to the final installment.
Example:
100.00 over 3 installments becomes:
33.33
33.33
33.34

10. Add projection/view model if appropriate
Add a non-persistent projection/view model such as `InstallmentProjection` for UI/reporting use.

It should include:
- provider name
- plan name
- installment number
- installment date
- installment amount
- credit card name
- statement cycle start date
- statement cycle end date
- cash flow due date
- cash flow period

Important constraints:
- Keep MVP 1 simple.
- No database schema is required yet.
- Prefer conceptual clarity over over-engineering.
- The output should remain markdown.
- Do not introduce frameworks or ORM concepts.
- Preserve the existing intent and structure where possible.
- Add clear examples where they help prevent ambiguity.

After updating the markdown, also add a short “Implementation Notes for Python” section recommending:
- dataclasses
- Decimal for money
- date objects for dates
- enums or constants for installment frequency
- pure functions for schedule generation and statement/due-date calculation

Follow-up instruction:
Ensure examples use `first_installment_date` instead of `start_date`.
```
