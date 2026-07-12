# UI Design Principles

## Purpose

Every future UI decision for the BNPL Cash Flow Tracker should align with the principles in this document.

When design trade-offs occur, this document takes precedence over personal preference.

The objective is consistency, usability, accessibility, and trust.

---

## Design Philosophy

The BNPL Cash Flow Tracker follows a hybrid design philosophy inspired by two industry-leading design systems:

- Apple Human Interface Guidelines (HIG)
- Google Material Design 3 (Material You / Material 3 Expressive)

The application combines Apple's emphasis on:

- Clarity
- Deference
- Depth

with Google's emphasis on:

- Friendly interactions
- Modern components
- Accessibility
- Expressive but restrained interfaces

The goal is to create an application that feels modern, approachable, and trustworthy while keeping financial information easy to understand.

---

## Design Goals

The application should feel:

- approachable
- trustworthy
- calm
- modern
- lightweight
- visually clean
- welcoming

Users should feel guided rather than instructed.

the interface should help users feel confident and informed when working with personal finances.
---

## Core Principles

### Clarity

Financial information is always the primary focus.

The interface should remove distractions rather than add them.

Users should understand what to do next without needing instructions.

### Simplicity

Every screen should have one primary objective.

Avoid asking for unnecessary information.

Avoid overwhelming users with large forms.

### Progressive Disclosure

Only show information when it becomes relevant.

Collect information step by step.

Never expose advanced concepts before they are needed.

### Consistency

Use consistent spacing, typography, terminology, colors, and interaction patterns throughout the application.

Users should never need to relearn the interface.

### Trust

Financial software must inspire confidence.

Animations and visual styling should support usability rather than distract from it.

Accuracy always takes priority over aesthetics.

---

## User Experience Principles

The application should:

- guide users through a workflow
- reduce cognitive load
- provide immediate feedback
- explain validation errors clearly
- celebrate successful completion
- keep navigation simple

Avoid technical language where possible.

Use friendly human language instead.

Example:

Instead of:

Validation Error

Prefer:

Let's fix a few things before we continue.

---

## Visual Design Principles

The interface should favor:

- generous whitespace
- rounded components
- card-based layouts
- readable typography
- subtle shadows
- clean alignment
- strong visual hierarchy

Prefer cards over tables wherever practical.

Use tables only when comparing structured financial information.

---

## Interaction Principles

The UI should:

- ask one question per screen whenever practical
- use progress indicators for multi-step workflows
- minimize typing
- prefer dropdowns over manual entry when possible
- provide sensible defaults
- allow users to review information before generating reports

---

## Accessibility Principles

Follow modern accessibility best practices.

Prioritize:

- high color contrast
- readable font sizes
- keyboard accessibility
- descriptive labels
- consistent navigation
- accessible color usage

Accessibility is a core requirement, not an enhancement.

---

## Information Hierarchy

Always prioritize information in this order:

1. Current financial position
2. Upcoming financial obligations
3. Statement impacts
4. Installment schedules
5. Supporting details

The interface should present the most actionable information first.

---
## Financial-First Design

The application exists to help users make better financial decisions.

Every screen should answer one or more of the following questions:

- What do I owe?
- When do I owe it?
- Which credit card will be affected?
- Which statement will include the charge?
- How will this purchase affect my future cash flow?

If a UI element does not help answer these questions or improve the user experience, it should be reconsidered.

Financial decision-making always takes priority over decorative features.

---
## What We Avoid

Avoid interfaces that resemble:

- banking portals
- enterprise software
- accounting systems
- spreadsheets
- developer tools

Avoid:

- unnecessary dialogs
- dense forms
- information overload
- excessive animations
- decorative graphics that reduce readability

---

## Decision Framework

When evaluating a UI decision, ask:

1. Does it improve clarity?
2. Does it reduce cognitive load?
3. Does it help users make better financial decisions?
4. Does it preserve trust?
5. Does it align with Apple Human Interface Guidelines?
6. Does it align with Google Material Design 3?

If the answer to most questions is yes, the design decision is likely appropriate.

---

## Relationship to MVPs

This document is intentionally independent of MVP scope.

All future MVPs should follow these principles.

The implementation may evolve, but the design philosophy should remain consistent.

---
## Relationship to the Backend

The user interface is a presentation layer only.

The UI may:

- collect user input
- display validation errors
- display reports
- guide users through workflows

The UI must never:

- perform financial calculations
- duplicate business rules
- duplicate validation rules
- determine statement cycles
- determine due dates
- aggregate cash-flow obligations

All financial logic remains the responsibility of the approved backend architecture.

---

## Acceptance Criteria

The document should:

- establish a long-term UI philosophy
- reference Apple Human Interface Guidelines and Google Material Design 3
- define principles instead of implementation
- be applicable to every future UI
- avoid framework-specific guidance
- serve as the project's long-term design constitution

