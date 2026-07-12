# MVP 3 UI Scope

## Objective

MVP 3 introduces a lightweight local graphical interface that allows users to enter credit cards and BNPL plans without manually editing JSON files.

The UI exists to improve usability, not to replace or modify the backend.

## Product Vision

"A friendly, guided experience that helps users understand how Buy Now Pay Later purchases affect future credit-card statements and cash flow."

The emphasis is on clarity, simplicity, and confidence.

## User Problem

Today the backend works correctly, but users must:

- manually create JSON
- understand the JSON contract
- run a CLI command

Most users are uncomfortable with this workflow.

The UI should guide users through the process one step at a time.

## In Scope

MVP 3 includes:

- Streamlit-based local UI
- Guided multi-step workflow
- Credit card setup
- BNPL plan setup
- Existing balance entry
- Add/remove BNPL plans
- Dropdown selection of credit cards
- Generate report
- Display backend results

The UI must reuse the existing MVP 2 application service.

## Out of Scope

MVP 3 does not include:

- New calculation rules
- Database
- User accounts
- Authentication
- Cloud deployment
- REST APIs
- Mobile applications
- Bank integrations
- Open Banking
- Notifications
- Payment tracking
- Interest calculations
- Budgeting
- AI features

## Guiding Principles

- One task per screen.
- Minimal cognitive load.
- Friendly language.
- Simple navigation.
- Progressive disclosure.
- Backend remains the single source of truth.
- The UI collects information but never performs calculations.

## Success Definition

MVP 3 is successful when a user can:

1. Launch the application locally.
2. Enter their credit cards.
3. Enter one or more BNPL plans.
4. Generate a report without writing JSON.
5. Receive exactly the same calculation results already validated in MVP 2.

## Acceptance Criteria

The document should clearly state:

- MVP 3 is a usability enhancement.
- MVP 2 remains the calculation engine.
- No new financial rules are introduced.
- The UI is intentionally simple and local.
