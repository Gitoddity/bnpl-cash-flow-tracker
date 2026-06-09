# Prompt 008 - Success Criteria Alignment

Date: 2026-06-09

## Full Prompt

```text
Review and update docs/success-criteria.md to align it with the approved MVP 1 Data Model, Calculation Rules, User Flows, and Test Cases.

Goal

Make only consistency and traceability improvements. Do not change any approved business rules or MVP scope.

Change 1: Align Cash Flow Aggregation Terminology

Current wording:

The engine must aggregate future obligations by:

- Due date.
- Credit card.
- Month.

Replace with:

The engine must aggregate future obligations by:

- Credit card.
- Payment due date.

Add clarification:

The engine must derive:

- cash_flow_year
- cash_flow_month
- cash_flow_period

from the payment due date.

Rationale:

The approved data model and calculation rules define aggregation by credit card and payment due date, while cash_flow_period is derived from the payment due date.

Change 2: Add Test Case Traceability

In Section 5 (Pass Automated Tests), add:

Automated tests should implement and validate the approved scenarios documented in docs/test-cases.md.

Add clarification that implementation is not considered complete until:

Automated tests pass locally.
Approved test-case scenarios pass successfully.

Rationale:

The approved business-rule test cases are now the source of truth for implementation validation.

Change 3: Align Human-Readable Output With InstallmentProjection

Current wording:

The engine must generate a local command-line report showing:

Replace with:

The engine must generate a human-readable report based on the InstallmentProjection view model.

Expected output should include:

- Installment date
- Installment amount
- Credit card
- Statement cycle
- Payment due date
- Cash-flow period
- Aggregated future obligations

Rationale:

The approved data model includes InstallmentProjection as the reporting-oriented projection model.

Constraints
Do not change business rules.
Do not change MVP scope.
Do not modify approved data model concepts.
Do not modify calculation rules.
Do not modify test cases.
Do not create implementation code.
Do not create Python files.
Do not create src/ or tests/ files.

Prompt History

Add:

Prompt 008 – Success Criteria Alignment

Update prompts/prompt-registry.md:

Date: 2026-06-09
Purpose: align success criteria with approved MVP 1 specifications
Outcome: success criteria reflect approved aggregation terminology, test-case traceability, and InstallmentProjection reporting
Related documents:
docs/data-model.md
docs/calculation-rules.md
docs/test-cases.md
docs/user-flows.md
Related prompts:
Prompt 002
Prompt 003
Prompt 004
Prompt 005
Prompt 006
Prompt 007

Acceptance Criteria
Aggregation terminology matches the approved data model and calculation rules.
Success criteria reference docs/test-cases.md.
Reporting criteria reference InstallmentProjection.
No business rules change.
No implementation files are created.
```
