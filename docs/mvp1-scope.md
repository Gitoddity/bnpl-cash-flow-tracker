# MVP 1 Scope

## Objective

MVP 1 will build and validate the BNPL Cash Flow Rules Engine.

The rules engine must answer this question:

```text
When will BNPL installments actually affect the user's cash flow through credit card payment due dates?
```

## In Scope

Business logic:

- Generate BNPL installment schedules.
- Assign installments to credit card statement cycles.
- Assign statement cycles to credit card payment due dates.
- Aggregate future obligations by payment due date.
- Aggregate future obligations by credit card.
- Derive cash-flow reporting fields:
  - `cash_flow_year`
  - `cash_flow_month`
  - `cash_flow_period`

Supported inputs:

- Credit card name.
- Credit card identifier.
- Credit card statement end day.
- Credit card payment due day.
- BNPL plan identifier.
- BNPL provider name.
- BNPL plan name.
- Purchase amount.
- Currency.
- Purchase date.
- First installment date.
- Installment count.
- Installment frequency.
- Linked credit card.

Expected outputs:

- Installment date.
- Installment amount.
- Statement cycle.
- Credit card due date.
- Aggregated future obligations by payment due date.
- Aggregated future obligations by credit card.
- Derived cash-flow reporting by:
  - `cash_flow_year`
  - `cash_flow_month`
  - `cash_flow_period`
- Human-readable reporting output based on `InstallmentProjection`.

Quality requirements:

- Automated tests for core rules.
- Real-world examples for Tangerine Mastercard, RBC Mastercard, Klarna Pay in 4, and PayPal Pay in 4.
- Clear documentation that remains aligned with implementation.

## Out Of Scope

MVP 1 must not build:

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
- Deployment infrastructure.

## Non-Goals

MVP 1 does not attempt to replace a budgeting app, banking app, or credit card portal. It focuses only on the calculation rules needed to transform BNPL installment dates into future credit card cash-flow obligations.

## Completion Boundary

MVP 1 is complete when:

- The rules engine can be executed locally.
- Automated tests pass.
- The approved scenarios documented in `docs/test-cases.md` are validated successfully.
- The output is human-readable.
- The implementation follows the documented data model and calculation rules.

`docs/test-cases.md` is the authoritative validation source for MVP 1 business-rule verification.
