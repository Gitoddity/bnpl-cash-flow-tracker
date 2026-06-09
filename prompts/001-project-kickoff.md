# Prompt 001 - Project Kickoff

Date: 2026-06-09

## Full Prompt

```text
# BNPL Cash Flow Tracker - MVP 1 Project Kickoff

IMPORTANT:

Before generating any implementation code:

1. Create all requested documentation.
2. Create project structure recommendations.
3. Create the prompt management structure.
4. Wait for review and approval before writing Python code.
5. Treat the documentation as the source of truth for future development.
6. Treat the prompt registry as the source of truth for project decision history.

You are acting as a Senior Product Manager, Solution Architect, Staff Software Engineer, Technical Writer, and Test Engineer.

---

# Project Overview

We are building a personal finance application called BNPL Cash Flow Tracker.

The purpose of the application is to help users understand the future cash-flow impact of Buy Now Pay Later (BNPL) purchases.

Existing BNPL applications typically show:

* Remaining balance
* Next payment date

However, they do not show:

* Which credit card statement an installment will appear on
* Which credit card payment due date will be affected
* The total future cash obligations across all BNPL plans
* Future monthly obligations across multiple BNPL providers

The key insight is:

BNPL installment date != cash impact date.

The actual cash impact occurs when the associated credit card bill becomes due.

The purpose of this application is to solve that problem.

---

# MVP 1 Objective

Build and validate the BNPL Cash Flow Rules Engine.

This MVP focuses exclusively on business logic and financial calculations.

The goal is to accurately calculate:

1. BNPL installment schedules
2. Credit card statement cycle assignment
3. Credit card due date assignment
4. Future cash-flow obligations
5. Aggregated future obligations across all BNPL plans

This MVP must be implemented as a Python-based rules engine.

No UI is required.

No database is required.

No API is required.

No cloud deployment is required.

The deliverable should be executable locally and validated through automated tests.

---

# Example Scenario

Credit Card:

* Name: Tangerine Mastercard
* Statement End Day: 17
* Payment Due Day: 13

BNPL Plan:

* Provider: Klarna
* Plan Name: Laptop Sleeve
* Purchase Amount: $120
* Start Date: June 7, 2026
* Installments: 4
* Frequency: Every 14 Days

Expected Output:

For each installment determine:

* Installment Date
* Installment Amount
* Statement Cycle
* Credit Card Due Date

And produce an aggregated cash-flow view grouped by due date.

---

# User Inputs

## Credit Card

The system must support:

* Card Name
* Statement End Day
* Payment Due Day

## BNPL Plan

The system must support:

* Provider Name
* Plan Name
* Purchase Amount
* Start Date
* Installment Count
* Installment Frequency
* Linked Credit Card

---

# Required Capabilities

## Installment Generation

Generate installment schedules automatically from:

* Purchase Amount
* Start Date
* Installment Count
* Frequency

## Statement Cycle Mapping

Determine which statement cycle each installment belongs to.

## Due Date Mapping

Determine which credit card payment due date each installment affects.

## Cash Flow Aggregation

Aggregate obligations by:

* Due Date
* Credit Card
* Month

---

# Deliverables

Create the following documentation first:

1. docs/product-requirements.md
2. docs/data-model.md
3. docs/calculation-rules.md
4. docs/user-flows.md
5. docs/mvp1-scope.md
6. docs/architecture.md
7. docs/success-criteria.md
8. docs/project-instructions.md

Create the following prompt management structure:

1. prompts/
2. prompts/prompt-registry.md
3. prompts/001-project-kickoff.md

Store this kickoff prompt in:

prompts/001-project-kickoff.md

Record the creation of this prompt in:

prompts/prompt-registry.md

---

# Prompt Management Requirements

This project must maintain a permanent record of all important AI prompts used throughout development.

Purpose:

The prompt registry serves as the historical record of all significant prompts that influenced:

* Product decisions
* Architecture decisions
* Domain model decisions
* Calculation rule decisions
* Testing decisions
* Implementation decisions

For every major prompt used during development:

* Record the date
* Record the prompt title
* Record the purpose
* Record the full prompt text
* Record key outcomes
* Record resulting decisions

Suggested prompt registry structure:

# Prompt Registry

## Prompt 001 - Project Kickoff

Date:
Purpose:

Prompt:
<full prompt>

Key Outcomes:
- Outcome 1
- Outcome 2

Decisions:
- Decision 1
- Decision 2

Examples of future prompt files:

prompts/
├── 001-project-kickoff.md
├── 002-domain-model-review.md
├── 003-rules-engine-design.md
├── 004-test-strategy.md
└── prompt-registry.md

AI Development Rule:

Whenever a prompt results in a significant architectural, domain-model, calculation-rule, testing, or implementation decision:

1. Save the prompt in the prompts folder.
2. Update prompt-registry.md.
3. Document resulting decisions.
4. Reference any related documentation that was modified.

The repository should remain self-documenting.

A future developer should be able to understand not only what was built, but why it was built by reviewing:

* Documentation
* Prompt history
* Recorded decisions

---

# project-instructions.md Requirements

This document must act as the long-term memory of the project.

Include:

## Product Vision

* Problem statement
* User problem
* Key insight
* Business value

## Domain Definitions

Definitions for:

* Credit Card
* Statement Cycle
* Due Date
* BNPL Plan
* Installment
* Cash Flow Obligation

## Architecture Principles

* Business logic first
* Testability first
* Simplicity first
* No premature optimization

## AI Development Rules

When generating code:

* Follow documented calculation rules
* Follow documented data model
* Prefer small incremental changes
* Create tests for new business logic
* Do not modify unrelated files
* Ask for clarification when requirements are ambiguous

## Documentation Rules

* Keep documentation current
* Update documentation before implementation when requirements change
* Maintain consistency between documentation and implementation

## Prompt Management Rules

* Record major prompts
* Record major decisions
* Maintain prompt registry
* Keep prompt history synchronized with project evolution

---

# Success Criteria

The rules engine must:

## 1. Generate Installments Correctly

Given:

* Start Date
* Installment Frequency
* Installment Count
* Purchase Amount

Generate all installment dates and amounts accurately.

## 2. Assign Statement Cycles Correctly

Each installment must be assigned to the correct statement cycle.

Edge cases around statement closing dates must be tested.

## 3. Assign Due Dates Correctly

Each installment must be assigned to the correct credit card due date.

## 4. Aggregate Cash Flow Correctly

The engine must produce future obligations grouped by:

* Due Date
* Credit Card
* Month

## 5. Pass Automated Tests

Automated tests must cover:

* Installment generation
* Statement cycle mapping
* Due date mapping
* Cash-flow aggregation

## 6. Validate Against Real-World Examples

The engine must successfully model:

* Tangerine Mastercard
* RBC Mastercard
* Klarna Pay in 4
* PayPal Pay in 4

## 7. Produce Human-Readable Output

Generate a command-line report showing:

* Installment Date
* Installment Amount
* Statement Cycle
* Due Date

And aggregated future obligations.

---

# Out of Scope

Do not build:

* Authentication
* User accounts
* Database persistence
* APIs
* React UI
* Mobile applications
* Notifications
* Budgeting features
* Investment tracking
* Credit score tracking
* Bank integrations
* Plaid integrations
* Open Banking integrations
* AI features

---

# Technical Expectations

Recommend:

* Project structure
* Domain model design
* Rules engine architecture
* Testing strategy

Use clean architecture principles where appropriate.

Prefer simplicity, correctness, readability, and testability over premature optimization.

Do not generate a UI.

Do not generate deployment infrastructure.

Focus entirely on creating a robust and well-tested finance rules engine that can serve as the foundation for future MVPs.

After generating all documentation, stop and wait for review and approval before producing any implementation code.
```
