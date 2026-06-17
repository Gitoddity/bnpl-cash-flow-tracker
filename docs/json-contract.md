# MVP 2 JSON Contract

## Overview

MVP 2 accepts one canonical JSON payload that describes credit cards and BNPL plans.

The contract is intentionally strict:

- It is machine-readable.
- It is validation-friendly.
- It maps directly to the existing domain model.
- It avoids duplicating calculation logic.

## Top-Level Shape

```json
{
  "credit_cards": [],
  "bnpl_plans": [],
  "output_options": {}
}
```

## Top-Level Fields

### `credit_cards`

Required array of credit-card objects.

Each item defines a reusable card that BNPL plans may reference by `credit_card_id`.

### `bnpl_plans`

Required array of BNPL plan objects.

Each item defines a purchase and references one `credit_card_id`.

### `output_options`

Optional object that controls presentation preferences.

This field must not affect calculations.

Suggested keys:

- `include_installment_schedule`
- `include_installment_projections`
- `include_cash_flow_obligations`
- `sort_output`

If omitted, the application should use sensible defaults and render the standard report.

## Credit Card Object

```json
{
  "id": "card_tangerine_mastercard",
  "name": "Tangerine Mastercard",
  "statement_end_day": 17,
  "payment_due_day": 13
}
```

### Fields

- `id`: string, required, stable internal identifier.
- `name`: string, required, human-readable card name.
- `statement_end_day`: integer, required, 1 to 31.
- `payment_due_day`: integer, required, 1 to 31.

### Rules

- `id` must be unique across all cards.
- `statement_end_day` and `payment_due_day` must be positive integers.
- The application layer must pass the values to the existing `CreditCard` domain model.

## BNPL Plan Object

```json
{
  "id": "plan_klarna_laptop_sleeve",
  "provider_name": "Klarna",
  "plan_name": "Laptop Sleeve",
  "purchase_amount": "120.00",
  "currency": "CAD",
  "purchase_date": "2026-06-07",
  "first_installment_date": "2026-06-07",
  "installment_count": 4,
  "installment_frequency": "BIWEEKLY",
  "credit_card_id": "card_tangerine_mastercard"
}
```

### Fields

- `id`: string, required, stable internal identifier.
- `provider_name`: string, required.
- `plan_name`: string, required.
- `purchase_amount`: string, required, decimal money value.
- `currency`: string, required, ISO-style currency code such as `CAD`.
- `purchase_date`: string, required, `YYYY-MM-DD`.
- `first_installment_date`: string, required, `YYYY-MM-DD`.
- `installment_count`: integer, required, greater than zero.
- `installment_frequency`: string, required, one of `BIWEEKLY`, `WEEKLY`, or `MONTHLY`.
- `credit_card_id`: string, required, must reference an existing card.

### Rules

- `purchase_amount` must be parsed as `Decimal`, not floating point.
- `purchase_date` and `first_installment_date` are separate fields even if they are the same date.
- MVP 2 must support the existing MVP 1 `BIWEEKLY` frequency and may accept future-ready values only if the application layer explicitly rejects or defers unsupported calculations.
- The application layer must preserve the existing engine’s behavior for installment rounding and schedule generation.

## Input Examples

### Single Card, Single Plan

```json
{
  "credit_cards": [
    {
      "id": "card_tangerine_mastercard",
      "name": "Tangerine Mastercard",
      "statement_end_day": 17,
      "payment_due_day": 13
    }
  ],
  "bnpl_plans": [
    {
      "id": "plan_klarna_laptop_sleeve",
      "provider_name": "Klarna",
      "plan_name": "Laptop Sleeve",
      "purchase_amount": "120.00",
      "currency": "CAD",
      "purchase_date": "2026-06-07",
      "first_installment_date": "2026-06-07",
      "installment_count": 4,
      "installment_frequency": "BIWEEKLY",
      "credit_card_id": "card_tangerine_mastercard"
    }
  ]
}
```

### Multiple Cards, Multiple Plans

```json
{
  "credit_cards": [
    {
      "id": "card_tangerine_mastercard",
      "name": "Tangerine Mastercard",
      "statement_end_day": 17,
      "payment_due_day": 13
    },
    {
      "id": "card_rbc_mastercard",
      "name": "RBC Mastercard",
      "statement_end_day": 6,
      "payment_due_day": 27
    }
  ],
  "bnpl_plans": [
    {
      "id": "plan_tangerine_shared_date",
      "provider_name": "Klarna",
      "plan_name": "Tangerine Shared Date",
      "purchase_amount": "40.00",
      "currency": "CAD",
      "purchase_date": "2026-06-12",
      "first_installment_date": "2026-06-12",
      "installment_count": 1,
      "installment_frequency": "BIWEEKLY",
      "credit_card_id": "card_tangerine_mastercard"
    },
    {
      "id": "plan_rbc_shared_date",
      "provider_name": "PayPal",
      "plan_name": "RBC Shared Date",
      "purchase_amount": "60.00",
      "currency": "CAD",
      "purchase_date": "2026-06-12",
      "first_installment_date": "2026-06-12",
      "installment_count": 1,
      "installment_frequency": "BIWEEKLY",
      "credit_card_id": "card_rbc_mastercard"
    }
  ]
}
```

## Validation Rules

The input layer must reject payloads that violate the contract.

### Required validation checks

- Missing top-level arrays.
- Duplicate card IDs.
- Duplicate plan IDs.
- Plan references to missing cards.
- Non-string dates.
- Invalid date formats.
- Non-decimal purchase amounts.
- Negative or zero amounts.
- Missing required fields.
- Unsupported or malformed installment frequencies.
- Invalid day-of-month values.

### Reference validation

Each BNPL plan must reference a real card by `credit_card_id`.

The application must fail fast if a referenced card does not exist.

## Parsing Rules

- Dates must parse as `datetime.date`.
- Money must parse as `Decimal`.
- IDs and names must remain strings.
- No calculation functions may parse JSON directly.

## Output Contract

The input contract feeds the application service, which returns:

- Parsed domain objects.
- Installment schedules.
- Statement-cycle assignments.
- Due-date assignments.
- Cash-flow obligations.
- InstallmentProjection objects.
- Human-readable CLI output.

The JSON contract itself does not define the rendered text, only the structured data needed to produce it.

