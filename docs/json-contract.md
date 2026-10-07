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

Must contain at least one item.

Each item defines a reusable card that BNPL plans may reference by `credit_card_id`.

The application reads the current date from the system clock at runtime. Users must not provide a current date in the JSON payload. The runtime date anchors the active statement cycle and is displayed in the generated report.

### `bnpl_plans`

Required array of BNPL plan objects.

Must contain at least one item.

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
  "profile_id": "profile_1",
  "name": "Tangerine Mastercard",
  "statement_end_day": 17,
  "payment_due_day": 13,
  "current_balance": "500.00",
  "current_balance_due_date": "2026-08-13"
}
```

### Fields

- `id`: string, required, stable internal identifier.
- `profile_id`: string, stable owner identifier. The financial contract carries it because `CreditCard` requires stable profile ownership; financial calculations do not use it. Omitted legacy payloads normalize to `profile_1`.
- `name`: string, required, human-readable card name.
- `statement_end_day`: integer, required, 1 to 31.
- `payment_due_day`: integer, required, 1 to 31.
- `current_balance`: string, optional, decimal money value, defaults to `0.00` when omitted.
- `current_balance_due_date`: string, optional, `YYYY-MM-DD`; assigns the current balance to a cash-flow due date.

### Rules

- `id` must be unique across all cards.
- `statement_end_day` and `payment_due_day` must be positive integers.
- The application layer must pass the values to the existing `CreditCard` domain model.
- `current_balance` must parse as `Decimal`.
- `current_balance` must be zero or positive.
- Negative balances and credit balances are not supported in MVP 2.
- `current_balance` must use the same currency as the BNPL plans in the payload.
- When `current_balance_due_date` is provided for a positive balance, that balance must appear in cash-flow obligations on the specified date.
- Legacy payloads may use `existing_balance`; it is normalized to `current_balance`. Supplying both fields is invalid.

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
  "paid_installment_count": 2,
  "amount_paid": "60.00",
  "installment_frequency": "BIWEEKLY",
  "credit_card_id": "card_tangerine_mastercard"
}
```

### Fields

- `id`: string, required, stable internal identifier.
- `provider_name`: string, required.
- `plan_name`: string, required.
- `purchase_amount`: string, required, decimal money value.
- `currency`: string, required, supported values are `CAD` and `USD`.
- `purchase_date`: string, required, `YYYY-MM-DD`.
- `first_installment_date`: string, required, `YYYY-MM-DD`.
- `installment_count`: integer, required, greater than zero.
- `paid_installment_count`: integer, optional, defaults to `0`; must be between `0` and `installment_count`.
- `amount_paid`: decimal string, optional, defaults to `"0.00"`; records the provider's exact completed-payment total.
- `installment_frequency`: string, required.
- Supported values:
  - `BIWEEKLY`.
- `credit_card_id`: string, required, must reference an existing card.

### Rules

- `purchase_amount` must be parsed as `Decimal`, not floating point.
- `purchase_date` and `first_installment_date` are separate fields even if they are the same date.
- The application layer must preserve the existing engine's behavior for installment rounding and schedule generation.
- Installments numbered `1` through `paid_installment_count` are completed and must be excluded from projections and cash-flow obligations.
- When `amount_paid` is provided, remaining installments must reconcile exactly to `purchase_amount - amount_paid`.
- Unsupported currency values must be rejected.

## Normalization Rules

Normalization may perform mechanical transformations only.

Allowed normalization:

- Trimming leading and trailing whitespace.
- Converting currency codes to uppercase.
- Converting installment frequency values to uppercase.

Normalization must not:

- Infer missing values.
- Modify dates.
- Change monetary amounts.
- Apply business rules.
- Alter calculation behavior.

## Input Examples

### Single Card, Single Plan

```json
{
  "credit_cards": [
    {
      "id": "card_tangerine_mastercard",
      "name": "Tangerine Mastercard",
      "statement_end_day": 17,
      "payment_due_day": 13,
      "current_balance": "500.00"
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
      "payment_due_day": 13,
      "current_balance": "500.00"
    },
    {
      "id": "card_rbc_mastercard",
      "name": "RBC Mastercard",
      "statement_end_day": 6,
      "payment_due_day": 27,
      "current_balance": "250.00"
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
- `installment_count` must be greater than zero.
- Missing required fields.
- Unsupported or malformed installment frequencies.
- Invalid day-of-month values.
- Unsupported currency values.
- Mixed-currency payloads.
- Negative current balances.

### Currency validation

- All BNPL plans within a single payload must use the same currency.
- Mixed-currency payloads are not supported in MVP 2.
- Validation must fail if more than one currency is detected within the same payload.
- Currency validation must be enforced after normalization and before calculation.

### Reference validation

Each BNPL plan must reference a real card by `credit_card_id`.

The application must fail fast if a referenced card does not exist.

### Current Balance Validation

- `current_balance` is optional.
- If omitted, `current_balance` defaults to `0.00`.
- If provided, `current_balance` must be a valid decimal string.
- If provided, `current_balance` must be greater than or equal to `0.00`.
- `current_balance` must use the same currency as the BNPL plans in the payload.
- Overpayments and credit balances are not supported in MVP 2.

## Parsing Rules

- Dates must parse as `datetime.date`.
- Money must parse as `Decimal`.
- IDs and names must remain strings.
- No calculation functions may parse JSON directly.
- After parsing and validation, domain objects become the source of truth.
- The rules engine operates on domain objects and must not access raw JSON directly.

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

## Validation Failure Behavior

### Validation Before Calculation

- JSON contract validation must happen before any MVP 1 calculation logic is invoked.
- The application must not invoke the rules engine if validation errors exist.
- Invalid input must fail fast at the input/application layer.
- The rules engine must only receive parsed, validated domain objects.

### Validation Error Reporting

Validation errors should clearly identify:

- The failed field or path, such as `bnpl_plans[0].currency`.
- The reason validation failed.
- The offending value when available.
- Multiple validation errors may be reported together where practical.

### Example Validation Failures

The following are examples of validation failures the input/application layer should catch:

- Missing required field: `bnpl_plans[0].purchase_amount` is required.
- Duplicate card ID: `credit_cards[1].id` duplicates `credit_cards[0].id`.
- Duplicate plan ID: `bnpl_plans[1].id` duplicates `bnpl_plans[0].id`.
- Invalid date format: `bnpl_plans[0].purchase_date = "06/07/2026"` is not a valid `YYYY-MM-DD` date.
- Unsupported currency: `bnpl_plans[0].currency = "EUR"` is not supported.
- Mixed-currency payload: `bnpl_plans[0].currency = "CAD"` and `bnpl_plans[1].currency = "USD"` are not allowed in the same payload.
- Missing credit card reference: `bnpl_plans[0].credit_card_id = "card_missing"` does not match any `credit_cards[].id`.
- Empty `credit_cards` array: `credit_cards` must contain at least one item.
- Empty `bnpl_plans` array: `bnpl_plans` must contain at least one item.
- Unsupported installment frequency: `bnpl_plans[0].installment_frequency = "DAILY"` is not supported.
- Invalid day-of-month value: `credit_cards[0].statement_end_day = 0` is outside the valid range.
- Non-decimal purchase amount: `bnpl_plans[0].purchase_amount = "abc"` is not a valid decimal value.
- Negative purchase amount: `bnpl_plans[0].purchase_amount = "-10.00"` must be rejected.
- Negative current balance: `credit_cards[0].current_balance = "-1.00"` must be rejected.

### Rules Engine Exception Boundary

- MVP 2 should not rely on rules-engine exceptions for normal input validation.
- Contract validation should catch invalid user input before calling the rules engine.
- Rules-engine exceptions should be treated as unexpected internal failures in MVP 2.
- Rules-engine exceptions may still occur if validated domain objects violate internal invariants, but that should indicate either:
  - a bug in validation,
  - a bug in domain-object construction,
  - or a previously undocumented invariant.
- The application layer may log rules-engine exceptions for diagnostic purposes.
- Internal implementation details should not be exposed directly to end users.

### No API-Style Error Schema

MVP 2 is a local CLI workflow, not an API.

Do not introduce:

- HTTP status codes.
- REST error payloads.
- API response schemas.
- Web UI error contracts.


## Payment plan providers (September 2026)

`provider_name` accepts `paypal`, `klarna`, `afterpay`, `sezzle`, and `affirm`.
JSON imports also accept formatted names (for example `PayPal`), normalize them
into these stable lowercase values, and reject arbitrary provider names.
Exports of new/imported plans contain stable values. Provider never determines
frequency: `installment_frequency` remains `BIWEEKLY`. CAD and USD are supported.
Version 1 portable profiles may contain both currencies; the overview reports
separate totals without conversion. Legacy CLI calculation payloads retain the
single-currency restriction described above.

The React API exposes GET/POST `/api/profiles/{profile_id}/plans` and GET
`/api/profiles/{profile_id}/export`. POST accepts decimal amounts as strings;
installment counts may be integers or whole-number strings, validated in Python.
`paid_installment_count` defaults to 0 and cannot exceed `installment_count`.
The linked card must belong to the requested profile. The existing version 1
`bnpl-profile` import endpoint accepts exported documents without modification.

The overview API also exposes GET `/api/profiles/{profile_id}/plans/overview`
and PATCH/DELETE `/api/profiles/{profile_id}/plans/{plan_id}`. See
[overview reporting and verification](payment-plans-overview.md) for schemas,
provider-charge definitions, and profile-isolation behavior. Derived reporting
fields are not part of the portable version 1 document.

Portable version 1 plans may also carry optional presentation fields `icon` and
`icon_color`, separate from financial inputs. Supported icons are `shopping`,
`laptop`, `home`, `plane`, `car`, `gift`, `heart`, `book`, `phone`, `music`, `coffee`,
and `star`; colors are `slate`, `blue`, `purple`, `pink`, `green`, and `orange`.
Omitted values display a slate shopping bag. Create/edit/import validate these
catalog values; export preserves them. Existing documents without these fields
remain supported and unchanged. Logos are derived from `provider_name`, not saved
as arbitrary URLs or image uploads.
