# MVP 3 UI Architecture

## Overview

MVP 3 adds a presentation layer only.

The Streamlit UI is responsible for guiding a user through the data-entry workflow and rendering the final report-ready output. It does not replace, reimplement, or weaken the existing MVP 2 backend.

The existing MVP 2 backend remains the source of truth for:

- JSON-compatible input structures
- input validation and normalization
- application-service orchestration
- the approved rules engine
- report-ready results
- CLI execution

The UI exists to improve usability by collecting user information and presenting results in a friendlier local experience.

## Architectural Principles

The following principles define the MVP 3 architecture:

- The UI must not perform financial calculations.
- The UI must not duplicate backend validation rules.
- The UI must not call individual rules functions directly.
- The UI must communicate through the existing application-service boundary.
- Backend calculations must remain independent of Streamlit.
- The CLI and Streamlit UI must reuse the same backend workflow.

## Recommended Flow

```text
Streamlit Inputs
→ UI State
→ JSON-Compatible Payload
→ Existing Input Validation
→ Existing Application Service
→ Existing Rules Engine
→ Report-Ready Result
→ Streamlit Rendering
```

This flow preserves the existing MVP 2 responsibility split.

## UI Layer Responsibilities

The UI layer may:

- render the guided multi-step workflow
- collect credit-card information
- collect BNPL-plan information
- maintain temporary local session state
- add or remove BNPL-plan rows
- construct the existing JSON-compatible payload
- submit the payload to the backend
- display friendly validation errors
- display report-ready results

The UI layer must not:

- calculate installment amounts
- map installments to statement cycles
- calculate payment due dates
- aggregate cash-flow obligations
- modify calculated values
- create alternative validation rules
- persist user data
- call external services

## UI Payload Builder

The UI payload builder is a thin translation layer between the Streamlit form and the existing MVP 2 JSON contract.

It may:

- convert UI field values into the shape required by `docs/json-contract.md`
- assign stable internal IDs for cards and plans
- map credit-card dropdown selections to `credit_card_id`
- pass dates and monetary values in the expected contract format

It must not:

- infer missing financial values
- change amounts
- apply financial rules
- silently correct invalid input

All final validation remains owned by the existing input layer.

## Session State

Streamlit session state may temporarily hold:

- current wizard step
- number of credit cards
- card names
- card details
- BNPL plan rows
- selected cards
- generated results

Session state is temporary only.

It is not persistence.

Refreshing or closing the application may clear data.

## Application-Service Integration

The Streamlit UI must call the same validated backend workflow used by MVP 2, beginning with the existing input validation layer and continuing through the application service.

The UI should not bypass:

- JSON-contract validation
- normalization
- domain-object construction
- existing rules-engine orchestration

In other words, the UI is responsible for collecting input and presenting results, while the backend remains responsible for turning that input into trusted calculations and report-ready output.

## Results Rendering

The Streamlit results screen should consume structured, report-ready results.

It may render:

- card balance summaries
- upcoming cash-flow obligations
- statement impacts
- installment projections
- installment schedules

The UI must not recompute totals for presentation if the backend already provides them.

## Error Ownership

The ownership of validation and error handling should remain explicit:

- The input/application layers determine whether data is valid.
- The UI formats backend validation errors into friendly, readable messages.
- Unexpected internal failures should display a safe generic message.
- Internal stack traces should not be shown to normal users.

This keeps the UI responsible for clarity while preserving backend responsibility for correctness.

## Recommended Project Structure

A minimal structure for MVP 3 may look like this:

```text
src/
  bnpl_cashflow/
    ui/
      app.py
      state.py
      payload_builder.py
      screens/
        card_count.py
        card_names.py
        card_details.py
        bnpl_plans.py
        results.py
```

The exact file split may remain smaller if Streamlit does not require this level of separation.

Avoid unnecessary abstraction.

## Testing Boundaries

Testing should follow the architectural separation already established by MVP 1 and MVP 2:

- payload-builder tests verify UI-to-contract mapping
- state tests verify add/remove and navigation behavior where practical
- integration tests verify that UI-generated payloads work with the existing backend
- MVP 1 and MVP 2 tests remain authoritative for calculation and validation correctness
- UI tests must not duplicate rules-engine tests

## Out of Scope

MVP 3 architecture does not introduce:

- database persistence
- user accounts
- authentication
- REST APIs
- cloud deployment
- bank integrations
- mobile applications
- new financial rules

## Acceptance Criteria

The architecture document must clearly establish that:

- Streamlit is a presentation layer.
- MVP 2 remains the backend source of truth.
- The UI creates the existing JSON-compatible payload.
- The UI does not duplicate calculations or validation.
- CLI and UI reuse the same backend.
- Session state is temporary and not persistence.
- No new product scope is introduced.
