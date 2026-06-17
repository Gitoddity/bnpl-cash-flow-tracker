# MVP 2 Architecture

## Overview

MVP 2 adds a thin application and input layer around the approved MVP 1 rules engine.

The architecture principle remains unchanged:

- Business rules live only in the existing rules engine.
- Input parsing and orchestration are separate concerns.
- Reporting remains presentation-only.
- No API is introduced unless a later scope change justifies it.

## Recommended Flow

```text
JSON Input -> Input Validation -> Application Service -> Existing Rules Engine -> Reporting -> CLI Output
```

## What Stays The Same

The following components remain the source of truth and should not be duplicated:

- Domain models in `src/bnpl_cashflow/domain/`.
- Pure rule functions in `src/bnpl_cashflow/rules/`.
- Reporting renderers and projection builders in `src/bnpl_cashflow/reporting/`.
- Approved business scenarios in `docs/test-cases.md`.

The existing engine already covers:

- Installment generation.
- Statement cycle mapping.
- Due date mapping.
- Cash-flow aggregation.
- InstallmentProjection construction.
- Human-readable reporting.

## New Architectural Layers

### Input Layer

Purpose:

- Parse JSON payloads.
- Validate required fields and value types.
- Normalize user-provided data into domain-ready structures.

Responsibilities:

- Validate top-level payload shape.
- Parse dates into `datetime.date`.
- Parse money into `Decimal`.
- Validate enumerations such as installment frequency.
- Validate that plan references point to existing cards.

Non-responsibilities:

- No business-rule calculations.
- No statement-cycle or due-date logic.
- No report formatting.

### Application Layer

Purpose:

- Coordinate the workflow from parsed input to final output.

Responsibilities:

- Build domain objects from validated input.
- Call existing rules functions in the correct order.
- Handle multiple plans and multiple cards.
- Join outputs into a report-ready structure.

Non-responsibilities:

- No recalculation of business rules.
- No direct date-rule or money-rule logic.
- No formatting beyond orchestration of report data.

### Reporting Layer

Purpose:

- Render results for local human consumption.

Responsibilities:

- Display installment schedules.
- Display installment projections.
- Display cash-flow obligations.
- Present validation and error messages in a readable way.

Non-responsibilities:

- No rule decisions.
- No payload parsing.
- No schema enforcement.

### CLI Layer

Purpose:

- Provide the simplest local entrypoint for real user data.

Responsibilities:

- Read JSON from a file path or stdin.
- Call the application service.
- Print report output.
- Exit non-zero on validation or runtime failure.

Non-responsibilities:

- No interactive UX beyond local command execution.
- No persistence.
- No server process.

## Boundary Rules

1. `input/` may validate and normalize data, but it may not calculate installment amounts, statement cycles, due dates, or aggregation totals.
2. `application/` may orchestrate calculations, but it may not implement calculation logic that belongs in `rules/`.
3. `rules/` remains the only place where business rules are defined.
4. `reporting/` may format outputs, but it may not alter calculated values.

## Recommended Project Structure

```text
src/
  bnpl_cashflow/
    application/
      services.py
      models.py
    input/
      json_parser.py
      validation.py
    cli.py
    domain/
    rules/
    reporting/

tests/
  application/
  input/
  integration/
  unit/
  fixtures/
```

## API Decision

No REST API should be introduced in MVP 2.

Reason:

- The user need is local processing of real data.
- The smallest viable contract is a JSON file or stdin payload.
- API design adds transport and deployment concerns before the input contract is validated.

An API can be evaluated after the local JSON workflow is proven useful and stable.

## Data Ownership

- JSON contract ownership: `input/`
- Workflow ownership: `application/`
- Calculation ownership: `rules/`
- Presentation ownership: `reporting/`
- Execution ownership: `cli.py`

## Extension Points

Future growth can attach to the architecture without changing MVP 1 rules:

- YAML input can be added alongside JSON later.
- A Streamlit UI can reuse the same application service later.
- A REST API can reuse the same application service later.

These are deferred, not part of MVP 2.

