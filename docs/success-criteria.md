# Success Criteria

## 1. Generate Installments Correctly

Given:

- First installment date.
- Installment frequency.
- Installment count.
- Purchase amount.

The engine must:

- Generate the correct number of installments.
- Use `first_installment_date` as the first installment date.
- Apply the frequency consistently to future installments.
- Calculate installment amounts accurately using decimal-safe money handling.

## 2. Assign Statement Cycles Correctly

Each installment must be assigned to the correct credit card statement cycle.

Tests must cover:

- Installment before statement end day.
- Installment on statement end day.
- Installment after statement end day.
- Month transitions.
- Year transitions.

## 3. Assign Due Dates Correctly

Each installment must be assigned to the correct credit card payment due date through its statement cycle.

Tests must cover:

- Due date in the same month as statement close.
- Due date in the month after statement close.
- Different card configurations.

## 4. Aggregate Cash Flow Correctly

The engine must aggregate future obligations by:

- Credit card.
- Payment due date.

The engine must derive:

- `cash_flow_year`
- `cash_flow_month`
- `cash_flow_period`

from the payment due date.

Tests must cover:

- Multiple installments on the same due date.
- Multiple BNPL plans on the same credit card.
- Multiple credit cards.
- Calendar month grouping by due date.

## 5. Pass Automated Tests

Automated tests must cover:

- Installment generation.
- Statement cycle mapping.
- Due date mapping.
- Cash-flow aggregation.
- End-to-end example scenarios.

Automated tests should implement and validate the approved scenarios documented in `docs/test-cases.md`.

The implementation is not considered complete until:

- Automated tests pass locally.
- Approved test-case scenarios pass successfully.

## 6. Validate Real-World Examples

The engine must successfully model:

- Tangerine Mastercard.
- RBC Mastercard.
- Klarna Pay in 4.
- PayPal Pay in 4.

At minimum, the Tangerine Mastercard and Klarna Laptop Sleeve example must match the documented expected output in `docs/calculation-rules.md`.

The engine must successfully model the approved scenarios documented in `docs/test-cases.md`.

The documented test cases represent the authoritative expected outputs for validation of installment generation, statement-cycle mapping, due-date mapping, and cash-flow aggregation.

## 7. Produce Human-Readable Output

The engine must generate a human-readable report based on the `InstallmentProjection` view model.

- Installment date.
- Installment amount.
- Credit card.
- Statement cycle.
- Payment due date.
- Cash-flow period.
- Aggregated future obligations.

The output should be understandable without reading the source code.

## 8. Respect MVP Boundaries

The engine must not include:

- UI.
- Database.
- API.
- Cloud deployment.
- Authentication.
- Bank integrations.
- AI features.
