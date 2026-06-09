# Data Model

## Overview

MVP 1 uses a simple conceptual domain model focused on calculation correctness. The future Python implementation should prefer small, explicit value objects and dataclasses over complex frameworks.

No database schema is required for MVP 1. IDs described here are stable internal application identifiers, not database primary keys.

## Credit Card

Represents the card used to pay BNPL installments.

Fields:

- `id`: Stable internal credit card identifier.
- `name`: Human-readable card name.
- `statement_end_day`: Day of month when the statement closes.
- `payment_due_day`: Day of month when payment is due.

Rules:

- `statement_end_day` must be a valid calendar day for the statement month.
- `payment_due_day` must be a valid calendar day for the due month.
- MVP 1 assumes statement and due day values are provided as day-of-month integers.

Example:

```text
ID: card_tangerine_mastercard
Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

## Installment Frequency

Represents the interval between BNPL installments.

Supported values:

- `BIWEEKLY`: Every 14 days. Supported in MVP 1.
- `WEEKLY`: Every 7 days. Future-ready, not required for MVP 1.
- `MONTHLY`: Monthly interval. Future-ready, not required for MVP 1.

Rules:

- MVP 1 must implement `BIWEEKLY`.
- Frequency should be represented explicitly with an enum or constants in Python.
- Do not store vague free-text frequency values as the calculation source of truth.

## BNPL Plan

Represents a purchase financed through a BNPL provider.

Fields:

- `id`: Stable internal BNPL plan identifier.
- `provider_name`: BNPL provider, such as Klarna or PayPal.
- `plan_name`: Human-readable plan or purchase name.
- `purchase_amount`: Total purchase amount.
- `currency`: Currency code for the purchase amount.
- `purchase_date`: Date the purchase was made.
- `first_installment_date`: Date of the first installment.
- `installment_count`: Number of installments.
- `installment_frequency`: Explicit installment frequency value, such as `BIWEEKLY`.
- `credit_card_id`: Stable internal identifier of the linked credit card.

Rules:

- MVP 1 may use `CAD` as the default currency, but currency must be stored explicitly.
- `purchase_date` and `first_installment_date` may be the same in MVP 1, but the model must keep them separate.
- Installment 1 occurs on `first_installment_date`.
- MVP 1 supports `BIWEEKLY` installment frequency.
- The purchase amount is divided across installments using decimal-safe rounding rules.

Example:

```text
ID: plan_klarna_laptop_sleeve
Provider: Klarna
Plan Name: Laptop Sleeve
Purchase Amount: 120.00
Currency: CAD
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installments: 4
Installment Frequency: BIWEEKLY
Credit Card ID: card_tangerine_mastercard
```

## Installment

Represents a single scheduled BNPL payment.

Fields:

- `plan_id`: Stable internal identifier of the BNPL plan.
- `credit_card_id`: Stable internal identifier of the linked credit card.
- `installment_number`: One-based installment sequence number.
- `installment_date`: Date the BNPL provider charges the card.
- `installment_amount`: Amount charged for this installment.
- `currency`: Currency code for the installment amount.

Rules:

- Installments reference `plan_id` and `credit_card_id`; they do not rely only on provider, plan, or card names.
- `installment_date` is the credit card charge date used for statement cycle assignment.

Derived fields:

- `statement_cycle`.
- `cash_flow_due_date`.

## Statement Cycle

Represents the card statement period that captures a card charge.

Fields:

- `credit_card_id`.
- `cycle_start_date`.
- `cycle_end_date`.

Rules:

- A charge belongs to a statement cycle when `previous_cycle_end_date < charge_date <= cycle_end_date`.
- A charge dated on the statement end day belongs to that closing statement.
- `cycle_start_date` is the day after the previous cycle end date.

Example:

```text
Previous Cycle End: 2026-05-17
Cycle Start: 2026-05-18
Cycle End: 2026-06-17
Charge Date: 2026-06-17
Result: Charge belongs to the statement closing on 2026-06-17.
```

## Due Date

Represents the credit card payment due date affected by a statement cycle.

Fields:

- `credit_card_id`.
- `statement_cycle_end_date`.
- `payment_due_date`.

Rules:

- The due date is the first occurrence of `payment_due_day` after the statement cycle close date.
- The due date rule must be calculated from actual dates, not only by comparing due day and statement end day.

Example:

```text
Statement Cycle End: 2026-06-17
Payment Due Day: 13
Payment Due Date: 2026-07-13
```

```text
Statement Cycle End: 2026-06-10
Payment Due Day: 25
Payment Due Date: 2026-06-25
```

## Cash Flow Obligation

Represents the cash impact created by one or more installments due through a credit card payment.

Fields:

- `due_date`: Credit card payment due date.
- `credit_card_id`: Stable internal identifier of the linked credit card.
- `statement_cycle_end_date`: Statement close date that produced the obligation.
- `cash_flow_year`: Calendar year of the due date.
- `cash_flow_month`: Calendar month of the due date.
- `cash_flow_period`: Calendar year-month of the due date, such as `2026-07`.
- `currency`: Currency code for the obligation.
- `total_amount`: Total amount due for the aggregation group.
- `installments`: Installments included in the obligation.

Aggregation keys:

- Due date.
- Credit card.
- Cash-flow year-month.

Rules:

- `cash_flow_period` is based on the credit card payment due date, not the installment date.
- MVP 1 should use `YYYY-MM` formatting for `cash_flow_period`.

## Installment Projection

`InstallmentProjection` is a non-persistent view model for reporting or future UI display. It should be derived from domain objects and calculation results.

Fields:

- `provider_name`.
- `plan_name`.
- `installment_number`.
- `installment_date`.
- `installment_amount`.
- `currency`.
- `credit_card_name`.
- `statement_cycle_start_date`.
- `statement_cycle_end_date`.
- `cash_flow_due_date`.
- `cash_flow_period`.

Rules:

- This is not a database model.
- This should not be used as the source of truth for calculations.
- It exists to present calculated results in a human-readable format.

## Money Handling

The implementation must use decimal-safe money handling. Binary floating point must not be used for financial calculations.

Installment rounding rule:

- Divide purchase amount across installments.
- Round installment amounts to 2 decimal places.
- Assign any rounding remainder to the final installment.

Example:

```text
Purchase Amount: 100.00
Installments: 3

Installment 1: 33.33
Installment 2: 33.33
Installment 3: 33.34
```

## Implementation Notes For Python

Recommended implementation choices:

- Use `dataclasses` for simple domain objects.
- Use `Decimal` for money.
- Use `datetime.date` for dates.
- Use enums or constants for installment frequency.
- Use pure functions for schedule generation.
- Use pure functions for statement cycle calculation.
- Use pure functions for due date calculation.
- Use pure functions for cash-flow aggregation.

Avoid:

- Binary floating point for money.
- ORM concepts.
- Database schema assumptions.
- Framework-specific models.
- UI-specific fields in domain objects.
