# User Flows

## Overview

MVP 1 has no UI, database, API, or cloud deployment. User flows describe how a local command-line or script-driven rules engine should behave after implementation.

## Flow 0: Start Calculation Run

User goal:

- Run the BNPL Cash Flow Tracker calculation engine using one or more configured credit cards and BNPL plans.

Inputs:

- One or more credit cards.
- One or more BNPL plans.

Expected result:

- Inputs are validated.
- Installment schedules are generated.
- Installments are mapped to statement cycles.
- Statement cycles are mapped to payment due dates.
- Cash-flow obligations are aggregated.
- Installment projections are generated for reporting.

Example output:

```text
Calculation Run Started

Credit Cards Loaded: 2
BNPL Plans Loaded: 3

Generated:
- Installment Schedules
- Statement Cycle Mapping
- Due Date Mapping
- Cash Flow Obligations
- Installment Projections
```

## Flow 1: Define Credit Cards

User goal:

- Enter one or more credit cards used for BNPL payments.

Inputs:

- Card ID.
- Card name.
- Statement end day.
- Payment due day.

Expected result:

- The card can be referenced by BNPL plans.
- The card's statement and due-date rules are used in all calculations.

Example:

```text
Card ID: card_tangerine_mastercard
Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

## Flow 2: Define BNPL Plans

User goal:

- Enter BNPL purchase details.

Inputs:

- Plan ID.
- Provider name.
- Plan name.
- Purchase amount.
- Currency.
- Purchase date.
- First installment date.
- Installment count.
- Installment frequency.
- Linked credit card ID.

Expected result:

- The engine generates the full installment schedule.
- Each installment is linked to the selected card via `credit_card_id`.

Example:

```text
Plan ID: plan_klarna_laptop_sleeve
Provider: Klarna
Plan Name: Laptop Sleeve
Purchase Amount: 120.00
Currency: CAD
Purchase Date: 2026-06-07
First Installment Date: 2026-06-07
Installments: 4
Frequency: BIWEEKLY
Linked Credit Card ID: card_tangerine_mastercard
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
2026-06-07 installment -> 2026-07-13 payment due date
2026-06-21 installment -> 2026-08-13 payment due date
```

## Flow 6: Review Aggregated Cash Flow

User goal:

- See total future obligations grouped by payment due date, credit card, and cash-flow period.

Expected output:

```text
2026-07-13 | Tangerine Mastercard | 2026-07 | 30.00
2026-08-13 | Tangerine Mastercard | 2026-08 | 60.00
2026-09-13 | Tangerine Mastercard | 2026-09 | 30.00
```

## Flow 7: Review Installment Projection

User goal:

- See the complete calculated output for each installment.

Expected output:

```text
Installment Date
Installment Amount
Credit Card
Statement Cycle
Payment Due Date
Cash Flow Period
```

This flow represents the `InstallmentProjection` view model defined in the data model and is intended for reporting and future UI display.

## Flow 8: Validate Real-World Examples

User goal:

- Confirm the engine can model common BNPL and credit card scenarios.

Required scenarios:

- Tangerine Mastercard.
- RBC Mastercard.
- Klarna Pay in 4.
- PayPal Pay in 4.

Expected result:

- The generated schedules, statement cycles, due dates, and aggregations match documented expectations.
