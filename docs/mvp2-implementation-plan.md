# MVP 2 Implementation Plan

## Summary

MVP 2 will add a local JSON-driven application layer around the approved MVP 1 rules engine.

The implementation objective is not to change the financial rules. The objective is to make the rules engine usable with real user-provided data while keeping the calculation core untouched.

## Plan Principles

- Reuse the existing rules engine for all calculations.
- Do not duplicate business rules.
- Keep the input contract explicit and strict.
- Keep orchestration separate from calculation.
- Keep reporting separate from calculation.
- Defer APIs, UI, persistence, and integrations.

## Proposed Delivery Phases

### Phase 0: Contract Finalization

Deliverables:

- Approve the JSON contract in `docs/json-contract.md`.
- Approve the MVP 2 boundaries in `docs/mvp2-scope.md` and `docs/mvp2-architecture.md`.
- Confirm the existing MVP 1 engine remains the calculation source of truth.

Exit criteria:

- The team agrees on input shape, validation rules, and output expectations.

### Phase 1: Input Parsing And Validation

Deliverables:

- Parse JSON payloads into Python data structures.
- Validate top-level payload shape.
- Validate required fields, types, and value ranges.
- Parse dates and money into domain-safe types.
- Validate cross-object references between plans and cards.

Exit criteria:

- Invalid payloads fail fast with clear messages.
- Valid payloads can be converted into domain-ready objects.

### Phase 2: Application Service

Deliverables:

- Add a use-case service that receives validated input.
- Build existing domain objects from the payload.
- Call the existing MVP 1 rule functions in sequence:
  - installment generation,
  - statement-cycle mapping,
  - due-date mapping,
  - cash-flow aggregation,
  - projection construction.
- Combine results across multiple plans and cards.

Exit criteria:

- The service produces the same outputs as the current engine for the approved scenarios.
- No new calculation logic appears in the application layer.

### Phase 3: Reporting Integration

Deliverables:

- Reuse existing renderers for schedule and cash-flow output.
- Ensure output is deterministic and stable.
- Keep rendering logic presentation-only.

Exit criteria:

- Report output is understandable without reading source code.

### Phase 4: CLI Wrapper

Deliverables:

- Add a thin command-line entrypoint.
- Support input from a file path or stdin.
- Print the standard human-readable report.
- Return non-zero exit codes for validation and runtime failures.

Exit criteria:

- A user can run the workflow locally with JSON input and see readable results.

### Phase 5: Testing Expansion

Deliverables:

- Add input validation tests.
- Add application-layer orchestration tests.
- Add integration tests for full JSON-to-report flows.
- Preserve all existing MVP 1 tests unchanged.
- Tests should be added alongside implementation whenever practical.
- Phase 5 represents the final test expansion, integration verification, and regression pass.
- Testing is not intended to occur only after all implementation is complete.

Exit criteria:

- Existing MVP 1 tests still pass.
- New tests cover the new local workflow.

### Phase 6: Documentation Finalization

Deliverables:

- Update project documentation if any contract details change during implementation.
- Record any new decisions in the prompt registry.

Exit criteria:

- Documentation and implementation remain aligned.

## Recommended Module Additions

```text
src/bnpl_cashflow/
  application/
    services.py
    models.py
  input/
    json_parser.py
    validation.py
  cli.py
```

These modules are justified because they isolate the new responsibilities introduced by real user input.

## Testing Strategy

### Input Validation Tests

Focus:

- JSON parsing.
- Type conversion.
- Required field validation.
- Reference validation.
- Error handling.

Coverage examples:

- Missing `credit_cards`.
- Missing `bnpl_plans`.
- Duplicate IDs.
- Invalid dates.
- Invalid money strings.
- Unsupported frequency values.
- Missing referenced card.

### Application-Layer Tests

Focus:

- Correct orchestration of existing engine functions.
- Multiple plans per card.
- Multiple cards in one payload.
- Stable output ordering.

Coverage examples:

- TC-001 flow from JSON to obligations.
- Multi-card example.
- Multi-plan aggregation on the same due date.

### Integration Tests

Focus:

- End-to-end JSON file or stdin input.
- Output text stability.
- Preservation of MVP 1 behaviors.
- MVP 2 integration tests may use existing MVP 1 scenarios such as uneven rounding, year rollover, and leap-year cases.
- These tests verify preservation of approved MVP 1 behavior through the full workflow.
- MVP 2 integration tests do not become the source of truth for calculation correctness.
- Existing MVP 1 rule tests remain the authoritative verification of calculation logic.

Coverage examples:

- Tangerine Mastercard / Klarna Laptop Sleeve.
- Uneven rounding scenario.
- Year rollover scenario.
- Leap-year scenario.

### Regression Rule

The existing MVP 1 suite must remain intact and passing.

MVP 2 adds coverage around the new application and input layers, but it does not replace the original calculation tests.

## Success Criteria

MVP 2 is successful when all of the following are true:

1. A user can provide JSON input containing cards and plans.
2. The system validates the input before any calculations run.
3. The system reuses the existing MVP 1 engine for all business logic.
4. The output matches approved MVP 1 behavior.
5. The CLI works locally without requiring a server, database, or UI.
6. The MVP 1 test suite still passes.
7. New tests cover input validation, orchestration, and end-to-end workflow.

## Risks

### Scope Creep

The most likely failure mode is adding UI or API work too early.

Mitigation:

- Keep MVP 2 local and JSON-driven.
- Defer Streamlit, REST, and persistence.

### Rule Duplication

The most serious technical risk is reimplementing calculations in the application layer.

Mitigation:

- Make the application layer a coordinator only.
- Keep all business rules in `rules/`.

### Contract Drift

If the JSON payload becomes loosely defined, later implementation will be harder to validate.

Mitigation:

- Keep one canonical JSON contract.
- Test it with fixtures.

### Reporting Leakage

Formatting code can accidentally absorb business logic.

Mitigation:

- Keep reporting read-only and presentation-focused.
