# Prompt 007 - User Flows Workflow Entry Point Update

Date: 2026-06-09

## Full Prompt

```text
Review and update `docs/user-flows.md` to align it with the approved MVP 1 Data Model, Calculation Rules, and Test Cases.

## Goal

The document is already largely correct. This update should focus on consistency and completeness, not redesign.

## Change 1: Align User Flows With Stable IDs

The approved data model introduced stable internal identifiers.

### Flow 1 – Define Credit Cards

Current Inputs:

```text
- Card name
- Statement end day
- Payment due day
```

Update to:

```text
- Card ID
- Card name
- Statement end day
- Payment due day
```

Update the example accordingly:

```text
Card ID: card_tangerine_mastercard
Card Name: Tangerine Mastercard
Statement End Day: 17
Payment Due Day: 13
```

### Flow 2 – Define BNPL Plans

Current Inputs:

```text
- Provider name
- Plan name
- Purchase amount
- Purchase date
- First installment date
- Installment count
- Installment frequency
- Linked credit card
```

Update to:

```text
- Plan ID
- Provider name
- Plan name
- Purchase amount
- Currency
- Purchase date
- First installment date
- Installment count
- Installment frequency
- Linked credit card ID
```

Update the example accordingly.

## Change 2: Align Terminology With Data Model

Where appropriate:

* Use `credit_card_id` when describing references.
* Use `plan_id` when describing BNPL plans.
* Use `cash_flow_period` instead of generic month wording.

Example:

Current:

```text
See total future obligations grouped by due date, card, and month.
```

Replace with:

```text
See total future obligations grouped by payment due date, credit card, and cash-flow period.
```

## Change 3: Add Explicit Currency References

The approved data model stores currency explicitly.

Update examples to include:

```text
Currency: CAD
```

where applicable.

## Change 4: Add Flow For Reviewing Full Projection Output

Add a new flow after Flow 6:

### Flow 7: Review Installment Projection

User Goal:

* See the complete calculated output for each installment.

Expected Output:

```text
Installment Date
Installment Amount
Credit Card
Statement Cycle
Payment Due Date
Cash Flow Period
```

Explain that this flow represents the `InstallmentProjection` view model defined in the data model and is intended for reporting and future UI display.

## Change 5: Renumber Existing Flow 7

Current:

```text
Flow 7: Validate Real-World Examples
```

Rename to:

```text
Flow 8: Validate Real-World Examples
```

## Constraints

* Do not change approved business rules.
* Do not change approved data model concepts.
* Do not create implementation code.
* Do not create Python files.
* Do not create `src/` or `tests/` files.
* Keep the document focused on user behavior and expected outputs.

## Prompt History

Add Prompt 007 to prompt history and update the prompt registry.

Record:

* Date: 2026-06-09
* Purpose: align user flows with approved MVP 1 specifications
* Outcome: user flows reflect stable IDs, currency, cash-flow period terminology, and InstallmentProjection reporting flow
* Related documents:

  * docs/data-model.md
  * docs/calculation-rules.md
  * docs/test-cases.md

## Acceptance Criteria

* Flow 1 includes Card ID.
* Flow 2 includes Plan ID, Currency, and Linked Credit Card ID.
* Cash-flow terminology matches the approved data model.
* InstallmentProjection flow is documented.
* Real-world validation flow is preserved.
* No implementation files are created.
```
