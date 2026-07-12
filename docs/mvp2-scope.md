# MVP 2 Scope

## Objective

MVP 2 will make the existing MVP 1 BNPL cash-flow rules engine usable with real user-provided data.

The MVP 2 question is:

```text
How can a user provide their own BNPL and credit-card data, run it through the approved MVP 1 engine, and get a trustworthy cash-flow report locally?
```

## Product Vision

MVP 2 is a local, structured-input workflow for the BNPL Cash Flow Tracker. It lets a user supply card and BNPL plan data in JSON, validates that data, passes it to the existing rules engine, and renders human-readable results.

The product value is not new calculations. The value is making the approved calculations accessible to real data without changing the business rules.

## User Problem

Users can understand the MVP 1 calculations in theory, but they still cannot easily process their own data.

They need:

- A simple way to provide credit-card and BNPL plan data.
- Immediate validation of bad input.
- A reliable report that uses the approved calculation engine.

## In Scope

MVP 2 includes:

- JSON input for credit cards and BNPL plans.
- An existing credit card balance per card, defaulting to `0.00` when omitted.
- Showing BNPL impact alongside the existing card balance in report output.
- Input validation and normalization of JSON data only. No calculation corrections or business-rule adjustments occur during normalization.
- Application-layer orchestration across one or more cards and one or more plans.
- Reuse of the existing MVP 1 rules engine for all calculations.
- Human-readable reporting of installment schedules, projections, and cash-flow obligations.
- A thin CLI wrapper for local execution.
- Automated tests for the new input and orchestration layers.

## Out Of Scope

MVP 2 must not include:

- New business rules.
- Modification of MVP 1 domain rules
- Duplicate calculation logic.
- REST APIs.
- Streamlit or any other UI framework.
- Database persistence.
- Authentication.
- Cloud deployment.
- Bank integrations.
- Plaid or Open Banking integrations.
- Notifications.
- Budgeting features.
- AI features.
- Payment tracking.
- Interest calculation.
- Statement balance reconciliation.
- Minimum payment calculation.
- Credit-limit utilization.
- Transaction history import.

## Recommendation

The recommended MVP 2 path is:

```text
JSON Input -> Application Service -> Existing Rules Engine -> Reporting -> CLI Output
```

This is the smallest useful path because it:

- Reuses the approved MVP 1 engine instead of reimplementing calculations.
- Keeps the contract explicit and machine-readable.
- Avoids UI and API scope before the workflow is proven.
- Supports real user data with minimal architectural change.

## MVP 2 Goals

- Accept real user data in a strict JSON format.
- Validate references between plans and cards before calculation.
- Generate the same outputs already validated in MVP 1.
- Keep the engine deterministic and testable.
- Keep the reporting layer presentation-only.

## Non-Goals

- Building a public product surface.
- Supporting multiple input formats (CSV, Excel, YAML, etc.).
- Adding persistence or user accounts.
- Accepting free-form natural language input.
- Changing any rules for installment generation, statement-cycle mapping, due-date mapping, or cash-flow aggregation.

## Success Definition

MVP 2 is successful when a user can:

1. Provide JSON input containing cards and BNPL plans.
2. Run the local workflow.
3. Receive validated outputs produced by the existing MVP 1 engine.
4. See the same approved behaviors already covered by MVP 1 test cases.
