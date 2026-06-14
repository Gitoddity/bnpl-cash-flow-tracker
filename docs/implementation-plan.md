# BNPL Cash Flow Tracker MVP 1 Implementation Plan

## Summary

MVP 1 will be implemented as a small, deterministic Python rules engine that converts BNPL purchases into installment schedules, statement-cycle assignments, due-date mappings, and aggregated cash-flow obligations. The implementation will stay within the approved architecture and MVP scope: no UI, no API, no database, no cloud, and no business-rule changes.

This plan translates the approved source-of-truth docs into an execution roadmap for:
- core domain modeling,
- pure calculation rules,
- reporting/projection assembly,
- automated validation against the approved scenarios in `docs/test-cases.md`.

## Project Structure

The implementation will follow the approved structure from `docs/architecture.md`:

```text
src/
  bnpl_cashflow/
    domain/
    rules/
    reporting/

tests/
  unit/
  fixtures/
```

Implementation intent by layer:
- `domain/`: explicit value objects and dataclasses for cards, plans, installments, cycles, due dates, obligations, and `InstallmentProjection`.
- `rules/`: pure functions for installment generation, statement-cycle mapping, due-date mapping, and aggregation.
- `reporting/`: human-readable formatting and projection construction only, with no calculation logic.
- `tests/unit/`: focused tests for each rule and model behavior.
- `tests/fixtures/`: reusable scenario inputs and expected outputs derived from approved docs.

## Build Phases

### Phase 1 - Domain Models
Implement the core domain objects exactly as described in `docs/data-model.md`:
- `CreditCard`
- `BNPLPlan`
- `Installment`
- `StatementCycle`
- `DueDate`
- `CashFlowObligation`
- `InstallmentProjection`

This phase establishes:
- explicit fields,
- validation close to the model,
- decimal-safe money representation,
- date handling via `datetime.date`,
- frequency representation via enum or constants, with MVP 1 supporting `BIWEEKLY`.

### Phase 2 - Installment Generation Rules
Implement installment schedule generation in `rules/`:
- `BIWEEKLY` generation using 14-day increments.
- decimal-safe installment allocation using `Decimal`.
- final-installment remainder handling so totals always equal the original purchase amount.

This phase must satisfy the approved rounding behavior:
- round installments to 2 decimals,
- put any remainder into the final installment,
- preserve exact purchase total.

### Phase 3 - Statement Cycle Mapping
Implement statement-cycle assignment logic:
- determine the cycle containing each installment date,
- respect the boundary rule `previous_cycle_end_date < charge_date <= cycle_end_date`,
- handle:
  - before statement end day,
  - on statement end day,
  - after statement end day,
  - month transitions,
  - year transitions.

### Phase 4 - Due Date Mapping
Implement credit-card due-date calculation:
- calculate the first occurrence of the payment due day after statement close,
- support same-month and following-month due dates,
- keep the logic date-driven rather than comparing only day-of-month values.

### Phase 5 - Cash Flow Aggregation
Implement aggregation over generated installments and due dates:
- group by credit card,
- group by payment due date,
- derive:
  - `cash_flow_year`,
  - `cash_flow_month`,
  - `cash_flow_period`,
- ensure `cash_flow_period` uses `YYYY-MM` derived from the payment due date,
- keep aggregation deterministic and stable for repeated runs.

### Phase 6 - InstallmentProjection Construction
Implement projection assembly in `reporting/`:
- build `InstallmentProjection` objects from calculated installments and mappings,
- attach statement-cycle and due-date information,
- prepare reporting-friendly structures without moving business logic into formatting code.

### Phase 7 - Reporting
Implement human-readable output for:
- installment schedules,
- installment projection views,
- statement-cycle assignments,
- due-date assignments,
- aggregated cash-flow obligations.

Reporting must remain presentation-only and must not alter calculated values.

### Phase 8 - Automated Testing
Implement the automated test suite in parallel with the rules:
- unit tests for each model and pure function,
- scenario tests for end-to-end approved examples,
- fixture-driven checks for the canonical examples in `docs/test-cases.md`.

### Phase 9 - Validation
Validate every approved scenario in `docs/test-cases.md` against:
- generated installments,
- statement-cycle mapping,
- due-date mapping,
- aggregation totals,
- reporting-ready projections.

Validation is complete only when the approved scenarios produce the documented expected outputs.

## Testing Strategy

### Unit Testing Approach
Unit tests will cover each calculation step in isolation:
- installment schedule generation,
- decimal rounding and remainder handling,
- statement-cycle boundary behavior,
- due-date mapping,
- cash-flow aggregation,
- projection construction,
- basic model validation.

These tests should be small, deterministic, and focused on one behavior per test case.

### Scenario Testing Approach
Scenario tests will exercise the full pipeline from BNPL plan input to aggregated cash-flow output using the approved cases from `docs/test-cases.md`, including:
- Tangerine Mastercard standard Pay in 4 scenario,
- statement-end boundary cases,
- due-date same-month and following-month cases,
- uneven rounding case,
- multiple plans on the same card,
- multiple cards,
- year rollover,
- leap-year handling.

### Test Case Mapping to Phases
- Phase 1: model validation and field-level expectations.
- Phase 2: installment generation and rounding cases.
- Phase 3: statement-cycle boundary cases.
- Phase 4: due-date same-month and following-month cases.
- Phase 5: aggregation, multi-plan, multi-card, and period derivation cases.
- Phase 6: projection shape and reporting payload cases.
- Phases 7-9: full end-to-end scenario validation and human-readable output checks.

## Definition Of Done

MVP 1 implementation is complete only when all of the following are true:
- the implementation stays within the approved MVP scope in `docs/mvp1-scope.md`,
- the calculation behavior matches `docs/calculation-rules.md`,
- the domain model matches `docs/data-model.md`,
- every approved scenario in `docs/test-cases.md` passes,
- the completion boundary in `docs/mvp1-scope.md` is satisfied,
- the success criteria in `docs/success-criteria.md` are satisfied,
- automated tests pass locally,
- human-readable output is produced from `InstallmentProjection`,
- no unapproved architecture or business-rule changes were introduced.

## Risks And Assumptions

### Risks
- Date-boundary logic can regress if statement-cycle and due-date calculations are implemented inconsistently.
- Decimal rounding can drift if any step falls back to binary floating point.
- Aggregation errors can hide behind seemingly correct installment generation unless totals are explicitly tested.
- Projection/reporting code can accidentally absorb business logic unless layer boundaries are enforced.

### Assumptions
- MVP 1 supports only `BIWEEKLY` installment frequency.
- Currency is stored explicitly, with `CAD` as the practical default in the approved examples.
- The approved docs remain the source of truth; no rule changes are introduced during implementation.
- `InstallmentProjection` is a derived reporting view model, not a source-of-truth entity.
- `pytest` will be used for automated tests.
- The implementation will remain dependency-light and use standard library primitives where practical.
