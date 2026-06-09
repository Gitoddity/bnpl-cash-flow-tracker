# Project Instructions

## Product Vision

BNPL Cash Flow Tracker helps users understand the future cash-flow impact of Buy Now Pay Later purchases.

The user problem is that BNPL installment dates do not directly tell users when cash will be needed. When installments are paid with a credit card, the true cash impact happens when the associated credit card bill is due.

The key insight is:

```text
BNPL installment date != cash impact date
```

The business value is giving users a clear forward-looking view of future card payment obligations created by BNPL plans.

## Domain Definitions

Credit Card:

- The payment card used for BNPL installments.
- Defined by card name, statement end day, and payment due day.

Statement Cycle:

- The billing period that captures card charges.
- Includes charges after the previous statement end date through the current statement end date.

Due Date:

- The date when the credit card statement balance is due.
- This is the cash impact date for BNPL installments assigned to that statement cycle.

BNPL Plan:

- A purchase financed through a Buy Now Pay Later provider.
- Defined by provider, plan name, purchase amount, currency, purchase date, first installment date, installment count, frequency, and linked credit card.

Installment:

- A scheduled BNPL payment generated from a BNPL plan.
- Has an installment date and installment amount.

Cash Flow Obligation:

- The future cash requirement created by one or more installments assigned to a credit card due date.

## Architecture Principles

- Business logic first.
- Testability first.
- Simplicity first.
- No premature optimization.
- Prefer pure calculation functions.
- Keep formatting separate from calculations.
- Keep implementation aligned with documentation.

## AI Development Rules

When generating code:

- Follow documented calculation rules.
- Follow documented data model.
- Prefer small incremental changes.
- Create tests for new business logic.
- Do not modify unrelated files.
- Ask for clarification when requirements are ambiguous.
- Use decimal-safe money handling.
- Keep date calculations deterministic and testable.
- Do not add UI, database, API, cloud, or integration features unless the scope changes in documentation first.

## Documentation Rules

- Keep documentation current.
- Update documentation before implementation when requirements change.
- Maintain consistency between documentation and implementation.
- Treat documentation as the source of truth for MVP behavior.
- Record assumptions explicitly.
- Keep examples synchronized with tests.

## Prompt Management Rules

This project must maintain a permanent record of important AI prompts used throughout development.

For every major prompt that influences product, architecture, domain model, calculation rules, testing, or implementation:

- Save the prompt in the `prompts/` folder.
- Update `prompts/prompt-registry.md`.
- Record the date.
- Record the prompt title.
- Record the purpose.
- Record the full prompt text or a file reference to it.
- Record key outcomes.
- Record resulting decisions.
- Reference related documentation or implementation files that changed.

The prompt registry is the source of truth for project decision history.

## Source Of Truth Order

For future development:

1. `docs/project-instructions.md` defines long-term project rules.
2. `docs/calculation-rules.md` defines business calculation behavior.
3. `docs/data-model.md` defines core domain concepts.
4. `prompts/prompt-registry.md` records decision history.
5. Implementation must conform to the documents above.

## Current MVP Boundary

Before implementation begins, the documentation and prompt registry must be reviewed and approved.

No Python implementation should be created until approval is given.
