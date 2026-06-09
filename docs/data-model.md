# Data Model

## Overview

MVP 1 uses a simple conceptual domain model focused on calculation correctness. The future Python implementation should prefer small, explicit value objects and dataclasses over complex frameworks.

No database schema is required for MVP 1.

## Credit Card

Represents the card used to pay BNPL installments.

Fields:

- `name`: Human-readable card name.
- `statement_end_day`: Day of month when the statement closes.
- `payment_due_day`: Day of month when payment is due.

Rules:

- `statement_end_day` must be a valid calendar day for the statement month.
- `payment_due_day` must be a valid calendar day for the due month.
- MVP 1 assumes statement and due day values are provided as day-of-month integers.

Example:

```text
Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

## BNPL Plan

Represents a purchase financed through a BNPL provider.

Fields:

- `provider_name`: BNPL provider, such as Klarna or PayPal.
- `plan_name`: Human-readable plan or purchase name.
- `purchase_amount`: Total purchase amount.
- `start_date`: Date of the first installment.
- `installment_count`: Number of installments.
- `installment_frequency`: Frequency between installments.
- `linked_credit_card`: Credit card used to pay the installments.

Rules:

- Installment 1 occurs on `start_date`.
- MVP 1 supports fixed interval frequencies, starting with every 14 days.
- The purchase amount is divided equally across installments.

## Installment

Represents a single scheduled BNPL payment.

Fields:

- `provider_name`.
- `plan_name`.
- `installment_number`.
- `installment_date`.
- `installment_amount`.
- `linked_credit_card`.

Derived fields:

- `statement_cycle`.
- `cash_flow_due_date`.

## Statement Cycle

Represents the card statement period that captures a card charge.

Fields:

- `credit_card_name`.
- `cycle_start_date`.
- `cycle_end_date`.

Rules:

- A cycle includes charges after the previous statement end date through the current statement end date.
- An installment dated on the statement end day belongs to that closing statement.

Example:

```text
Cycle Start: 2026-05-18
Cycle End: 2026-06-17
```

## Due Date

Represents the credit card payment due date affected by a statement cycle.

Fields:

- `credit_card_name`.
- `statement_cycle_end_date`.
- `payment_due_date`.

Rules:

- The due date is the configured payment due day following the statement close date.
- If the due day is earlier in the month than the statement end day, the due date falls in the following month.

Example:

```text
Statement End: 2026-06-17
Payment Due Day: 13
Payment Due Date: 2026-07-13
```

## Cash Flow Obligation

Represents the cash impact created by one or more installments due through a credit card payment.

Fields:

- `due_date`.
- `credit_card_name`.
- `month`.
- `total_amount`.
- `installments`.

Aggregation keys:

- Due date.
- Credit card.
- Calendar month of the due date.

## Money Handling

The implementation should use decimal-safe money handling. Binary floating point must not be used for financial calculations.

MVP 1 should document and test how installment rounding is handled before implementation begins.
