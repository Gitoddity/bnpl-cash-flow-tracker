# Architecture

## Overview

MVP 1 should be implemented as a small Python rules engine with clear boundaries and no external application infrastructure.

The design priorities are:

- Correctness.
- Readability.
- Testability.
- Simplicity.
- Minimal dependencies.

## Recommended Project Structure

The repository should use this future implementation structure:

```text
docs/
prompts/
src/
  bnpl_cashflow/
    domain/
    rules/
    reporting/
tests/
  unit/
  fixtures/
```

Do not create implementation files until the documentation has been reviewed and approved.

## Domain Layer

Purpose:

- Represent core business concepts.
- Avoid framework or persistence concerns.

Recommended responsibilities:

- Credit card model.
- BNPL plan model.
- Installment model.
- Statement cycle model.
- Cash flow obligation model.

Implementation guidance:

- Prefer dataclasses or simple value objects.
- Keep validation explicit and close to the domain model.
- Use decimal-safe money handling.
- Avoid database-specific or UI-specific fields.

## Rules Layer

Purpose:

- Perform pure financial and calendar calculations.

Recommended responsibilities:

- Generate installment schedules.
- Map installment dates to statement cycles.
- Map statement cycles to payment due dates.
- Aggregate obligations by due date, credit card, and month.

Implementation guidance:

- Prefer deterministic pure functions.
- Keep functions small and directly testable.
- Do not read from or write to files inside calculation functions.
- Do not depend on system date except where explicitly provided.

## Reporting Layer

Purpose:

- Produce human-readable local output.

Recommended responsibilities:

- Render installment schedules.
- Render statement cycle assignments.
- Render due-date assignments.
- Render aggregated cash-flow summaries.

Implementation guidance:

- Keep formatting separate from calculations.
- Do not put business rules in report formatting code.

## Tests

Purpose:

- Validate the rules engine against documented behavior.

Recommended responsibilities:

- Unit tests for installment generation.
- Unit tests for statement cycle mapping.
- Unit tests for due date mapping.
- Unit tests for aggregation.
- Scenario tests for real-world examples.

Recommended fixtures:

- Tangerine Mastercard.
- RBC Mastercard.
- Klarna Pay in 4.
- PayPal Pay in 4.

## Dependency Policy

MVP 1 should use Python standard library features where practical.

Allowed future implementation concepts:

- `datetime.date` for dates.
- `decimal.Decimal` for money.
- `dataclasses` for simple domain objects.
- `pytest` for automated tests.

Avoid:

- Web frameworks.
- ORMs.
- Database clients.
- Frontend build tools.
- Cloud SDKs.

## Architecture Principles

- Business logic first.
- Testability first.
- Simplicity first.
- No premature optimization.
- Documentation is the source of truth.
- Prompt registry is the source of truth for decision history.
