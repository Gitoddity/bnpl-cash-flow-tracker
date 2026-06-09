# Product Requirements

## Product Vision

BNPL Cash Flow Tracker is a personal finance rules engine that helps users understand the future cash-flow impact of Buy Now Pay Later purchases.

Most BNPL and card apps show remaining balances and the next installment date. They usually do not show which credit card statement an installment lands on, which card payment due date is affected, or how multiple BNPL plans combine into future cash obligations.

The key insight for this product is:

```text
BNPL installment date != cash impact date
```

The actual cash impact occurs when the linked credit card bill becomes due.

## User Problem

Users who pay BNPL installments with credit cards need to know when cash will actually leave their budget. Installment dates alone are not enough because the cash impact depends on the credit card statement cycle and payment due date.

## MVP 1 Objective

MVP 1 will build and validate a Python-based BNPL cash-flow rules engine. It will focus only on business logic and financial calculations.

The engine must calculate:

- BNPL installment schedules.
- Credit card statement cycle assignment.
- Credit card payment due date assignment.
- Future cash-flow obligations.
- Aggregated future obligations across all BNPL plans.

## Target Users

MVP 1 is intended for personal finance users who need to understand upcoming credit-card payment obligations before payment due dates occur.

## Required Capabilities

The rules engine must support user-provided credit card information:

- Credit card identifier.
- Card name.
- Statement end day.
- Payment due day.

The rules engine must support user-provided BNPL plan information:

- BNPL plan identifier.
- Provider name.
- Plan name.
- Purchase amount.
- Currency.
- Purchase date.
- First installment date.
- Installment count.
- Installment frequency.
- Linked credit card.

The rules engine must produce:

- Installment date.
- Installment amount.
- Statement cycle.
- Credit card due date.
- Aggregated obligations by payment due date.
- Aggregated obligations by credit card.
- Derived cash-flow reporting by:
  - `cash_flow_year`
  - `cash_flow_month`
  - `cash_flow_period`

The rules engine must produce reporting output based on the `InstallmentProjection` view model containing:

- Installment date.
- Installment amount.
- Credit card.
- Statement cycle.
- Payment due date.
- Cash-flow period.

## Example Scenario

Credit card:

- Name: Tangerine Mastercard.
- Statement end day: 17.
- Payment due day: 13.

BNPL plan:

- Provider: Klarna.
- Plan name: Laptop Sleeve.
- Purchase amount: 120.00.
- Currency: CAD.
- Purchase date: 2026-06-07.
- First installment date: 2026-06-07.
- Installments: 4.
- Frequency: every 14 days.

Expected behavior:

- Generate four installments beginning on 2026-06-07.
- Assign each installment to the correct Tangerine Mastercard statement cycle.
- Assign each installment to the correct Tangerine Mastercard payment due date.
- Produce a cash-flow view grouped by payment due date.
- Validate approved scenarios documented in `docs/test-cases.md`.

## Out Of Scope

MVP 1 must not include:

- Authentication.
- User accounts.
- Database persistence.
- APIs.
- React UI.
- Mobile applications.
- Notifications.
- Budgeting features.
- Investment tracking.
- Credit score tracking.
- Bank integrations.
- Plaid integrations.
- Open Banking integrations.
- AI features.
- Cloud deployment.

## Expected Value

MVP 1 is successful when the rules engine can reliably explain the difference between BNPL installment timing and actual credit card cash impact timing. It should become the calculation foundation for later product versions.

The engine is considered validated when the approved scenarios documented in `docs/test-cases.md` pass successfully.
