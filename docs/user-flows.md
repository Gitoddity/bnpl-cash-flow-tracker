# User Flows

## Overview

MVP 1 has no UI, database, API, or cloud deployment. User flows describe how a local command-line or script-driven rules engine should behave after implementation.

## Flow 1: Define Credit Cards

User goal:

- Enter one or more credit cards used for BNPL payments.

Inputs:

- Card name.
- Statement end day.
- Payment due day.

Expected result:

- The card can be referenced by BNPL plans.
- The card's statement and due-date rules are used in all calculations.

Example:

```text
Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

## Flow 2: Define BNPL Plans

User goal:

- Enter BNPL purchase details.

Inputs:

- Provider name.
- Plan name.
- Purchase amount.
- Purchase date.
- First installment date.
- Installment count.
- Installment frequency.
- Linked credit card.

Expected result:

- The engine generates the full installment schedule.
- Each installment is linked to the selected card.

Example:

```text
Provider: Klarna
Plan Name: Laptop Sleeve
Purchase Amount: 120.00
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installments: 4
Frequency: BIWEEKLY
Linked Credit Card: Tangerine Mastercard
```

## Flow 3: Generate Installment Schedule

User goal:

- See the generated installment dates and amounts.

Expected output:

```text
Installment 1: 2026-06-07 - 30.00
Installment 2: 2026-06-21 - 30.00
Installment 3: 2026-07-05 - 30.00
Installment 4: 2026-07-19 - 30.00
```

## Flow 4: Map Installments To Statement Cycles

User goal:

- Understand which credit card statement each installment appears on.

Expected output:

```text
2026-06-07 -> Statement 2026-05-18 to 2026-06-17
2026-06-21 -> Statement 2026-06-18 to 2026-07-17
```

## Flow 5: Map Installments To Due Dates

User goal:

- Understand when each installment affects cash flow.

Expected output:

```text
2026-06-07 installment -> 2026-07-13 card payment due date
2026-06-21 installment -> 2026-08-13 card payment due date
```

## Flow 6: Review Aggregated Cash Flow

User goal:

- See total future obligations grouped by due date, card, and month.

Expected output:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 30.00
2026-08-13 | Tangerine Mastercard | 2026-08 | 60.00
2026-09-13 | Tangerine Mastercard | 2026-09 | 30.00
```

## Flow 7: Validate Real-World Examples

User goal:

- Confirm the engine can model common BNPL and credit card scenarios.

Required scenarios:

- Tangerine Mastercard.
- RBC Mastercard.
- Klarna Pay in 4.
- PayPal Pay in 4.

Expected result:

- The generated schedules, statement cycles, due dates, and aggregations match documented expectations.
