# Calculation Rules

## Overview

The rules engine converts BNPL installment schedules into credit card cash-flow obligations.

The calculation path is:

```text
BNPL Plan -> Installments -> Statement Cycles -> Due Dates -> Aggregated Cash Flow
```

## Installment Generation

Inputs:

- Purchase amount.
- First installment date.
- Installment count.
- Installment frequency.

Rules:

- Installment 1 occurs on `first_installment_date`.
- Each subsequent installment occurs one frequency interval after the previous installment.
- For Pay in 4 plans using a 14-day interval, installment dates are:
  - First installment date.
  - First installment date plus 14 days.
  - First installment date plus 28 days.
  - First installment date plus 42 days.
- MVP 1 supports `BIWEEKLY`, meaning every 14 days.
- Installment amounts are calculated by dividing purchase amount across installments, rounding to 2 decimal places, and assigning any remainder to the final installment.
- Implementation must use decimal-safe money handling. Binary floating point must not be used.

Example:

```text
Purchase Amount: 120.00
First Installment Date: 2026-06-07
Installments: 4
Frequency: BIWEEKLY

Installments:
1. 2026-06-07 - 30.00
2. 2026-06-21 - 30.00
3. 2026-07-05 - 30.00
4. 2026-07-19 - 30.00
```

### Rounding Example

```text
Purchase Amount: 100.00
Installments: 3

Installments:
1. 33.33
2. 33.33
3. 33.34
```

## Statement Cycle Mapping

Inputs:

- Installment date.
- Credit card statement end day.

Rules:

- A statement cycle includes charges where `previous_cycle_end_date < charge_date <= cycle_end_date`.
- An installment dated on the statement end day belongs to that closing statement.
- An installment dated after the statement end day belongs to the next statement cycle.

Example for statement end day 17:

```text
Cycle: 2026-05-18 through 2026-06-17
Installment Date: 2026-06-07
Assigned Cycle End: 2026-06-17
```

```text
Cycle: 2026-06-18 through 2026-07-17
Installment Date: 2026-06-21
Assigned Cycle End: 2026-07-17
```

## Due Date Mapping

Inputs:

- Statement cycle end date.
- Credit card payment due day.

Rules:

- The payment due date is the first occurrence of `payment_due_day` after the statement cycle close date.
- The due date rule must be calculated from actual dates, not only by comparing due day and statement end day.

Example for statement end day 17 and due day 13:

```text
Statement End: 2026-06-17
Due Day: 13
Payment Due Date: 2026-07-13
```

Example for statement end day 10 and due day 25:

```text
Statement End: 2026-06-10
Due Day: 25
Payment Due Date: 2026-06-25
```

## Cash Flow Aggregation

The engine must aggregate obligations by:

- Credit card.
- Payment due date.

Aggregation rules:

- Multiple installments assigned to the same card and due date should be summed.
- Multiple BNPL plans may contribute to the same due date.
- `cash_flow_year`, `cash_flow_month`, and `cash_flow_period` are derived from the payment due date.
- `cash_flow_period` uses the year-month of the payment due date.
- `cash_flow_period` uses `YYYY-MM` format, such as `2026-07`.

## Example: Tangerine Mastercard And Klarna

Credit card:

```text
Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

BNPL plan:

```text
Provider: Klarna
Plan Name: Laptop Sleeve
Purchase Amount: 120.00
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installments: 4
Frequency: BIWEEKLY
```

Generated installments:

```text
2026-06-07 - 30.00
2026-06-21 - 30.00
2026-07-05 - 30.00
2026-07-19 - 30.00
```

Expected mapping:

| Installment Date | Amount | Statement Cycle | Due Date |
| --- | ---: | --- | --- |
| 2026-06-07 | 30.00 | 2026-05-18 to 2026-06-17 | 2026-07-13 |
| 2026-06-21 | 30.00 | 2026-06-18 to 2026-07-17 | 2026-08-13 |
| 2026-07-05 | 30.00 | 2026-06-18 to 2026-07-17 | 2026-08-13 |
| 2026-07-19 | 30.00 | 2026-07-18 to 2026-08-17 | 2026-09-13 |

Aggregated cash flow:

| Due Date | Credit Card | Cash Flow Period | Total |
| --- | --- | --- | ---: |
| 2026-07-13 | Tangerine Mastercard | 2026-07 | 30.00 |
| 2026-08-13 | Tangerine Mastercard | 2026-08 | 60.00 |
| 2026-09-13 | Tangerine Mastercard | 2026-09 | 30.00 |

## Edge Cases To Test

- Installment date before statement end day.
- Installment date exactly on statement end day.
- Installment date after statement end day.
- Due date in the same calendar month as statement close.
- Due date in the following calendar month.
- Month-end and year-end transitions.
- Purchase amount that does not divide evenly across installments.
- Multiple BNPL plans assigned to the same card.
- Multiple cards with different statement and due days.
