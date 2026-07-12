# MVP 3 UI Implementation Plan

## 1. Overview

MVP 3 adds a local Streamlit interface that makes the existing MVP 2 backend easier to use without changing the backend's role.

The purpose of MVP 3 is to guide a user through a simple, personal-finance workflow:

```text
Welcome
→ Number of Credit Cards
→ Credit Card Names
→ Credit Card Details
→ BNPL Plan Entry
→ Review
→ Generate Projection
→ Results
```

The UI is a presentation layer only. It collects friendly input, preserves temporary session data, builds the existing JSON-compatible payload, hands that payload to the approved MVP 2 validation and application-service boundary, and renders the report-ready result returned by the backend.

MVP 3 depends on MVP 2 for the entire calculation and reporting chain:

- JSON contract validation
- normalization and payload validation
- application-service orchestration
- rules-engine execution
- structured backend results
- existing CLI-compatible workflow

This implementation plan therefore treats MVP 2 as the source of truth and Streamlit as a usability layer over an already validated backend.

The implementation-plan boundaries are intentionally narrow:

- no new business rules
- no duplicated validation
- no duplicated calculations
- no new persistence model
- no new reporting engine
- no transport or service-layer expansion beyond the local UI

## 2. Implementation Principles

The MVP 3 implementation should follow these principles:

- Presentation-layer separation
  - Streamlit is responsible for forms, navigation, state, and rendering only.
  - The backend remains responsible for validation, orchestration, calculation, and reporting output.

- Backend reuse
  - The UI should reuse the existing MVP 2 public workflow rather than new helpers.
  - The UI should call the same validation and application-service path already used by the CLI.

- Single source of truth
  - The approved backend remains the only source of correct financial behavior.
  - The UI may shape and present data, but it may not redefine the rules.

- Progressive wizard flow
  - The flow should feel guided, step-by-step, and focused on one task at a time.
  - Navigation should stay simple, local, and easy to review.

- Temporary session state
  - State is kept only while the user is actively using the app.
  - Active-session state is retained across navigation steps.
  - Refreshing, restarting, or intentionally resetting the session may clear it.

- Testability
  - UI behavior should be split into pure mapping and state-driven pieces where practical.
  - Tests should focus on payload construction, navigation, state transitions, stale-result handling, and integration with the approved backend workflow.

- Small reviewable phases
  - Implementation should be delivered in small, reviewable phases.
  - Each phase should have clear completion criteria and a review gate.

- No scope expansion
  - The UI must remain local and presentation-oriented.
  - No persistence, authentication, APIs, account features, integrations, or new business logic are added.

## 3. Proposed Project Structure

The repository already contains the backend-owned organization:

```text
src/
  bnpl_cashflow/
    application/
    input/
    domain/
    rules/
    reporting/
    cli.py
```

The UI should be added as a small sibling area under `src/bnpl_cashflow/ui/` rather than introducing a larger frontend architecture.

### Proposed new files

```text
src/
  bnpl_cashflow/
    ui/
      __init__.py
      app.py
      state.py
      payload_builder.py
      error_mapping.py
      screens.py
      results.py
```

### File-by-file responsibility

#### `src/bnpl_cashflow/ui/__init__.py`

Responsibility:

- Export the UI package entry points if needed.

Allowed dependencies:

- no heavy UI imports
- only package-level re-export where useful

Prohibited responsibilities:

- no form logic
- no business-rule logic
- no backend orchestration

#### `src/bnpl_cashflow/ui/app.py`

Responsibility:

- act as the Streamlit application entry point
- provide application orchestration for the wizard
- manage current-step dispatch
- coordinate navigation and session state
- generate the JSON-compatible payload from session state
- invoke the approved backend boundary
- manage the result lifecycle from generation through render

Allowed dependencies:

- Streamlit
- `state.py`
- `payload_builder.py`
- `error_mapping.py`
- `screens.py`
- `results.py`
- existing backend public entry points such as the input parser and application service

Prohibited responsibilities:

- no direct rendering of every individual form screen
- no calculation logic
- no business-rule validation
- no direct invocation of low-level rule functions
- no direct mutation of backend domain objects

#### `src/bnpl_cashflow/ui/state.py`

Responsibility:

- define the active-session state model
- provide helper functions for step transitions, add/remove plan behavior, and reset behavior
- manage temporary state keys and stale-result flags

Allowed dependencies:

- Python standard library only
- Streamlit session-state access only where needed

Prohibited responsibilities:

- no payload validation
- no financial computation
- no persistence beyond session state

#### `src/bnpl_cashflow/ui/payload_builder.py`

Responsibility:

- build the existing JSON-compatible MVP 2 payload from session-state data
- map user-facing field values to the approved JSON contract shape
- preserve stable internal card IDs and plan IDs in the payload
- keep the mapping function pure and independently testable where practical

Allowed dependencies:

- standard Python types and data structures
- the approved contract structure defined in `docs/json-contract.md`

Prohibited responsibilities:

- no business-rule validation
- no date or amount normalization beyond contract-aligned transformation
- no currency conversion
- no access to Streamlit runtime objects if it can be avoided

#### `src/bnpl_cashflow/ui/error_mapping.py`

Responsibility:

- convert backend validation issues into friendly user-facing messages
- map backend validation paths into friendly screen-level feedback
- preserve the backend's meaning while improving readability

Allowed dependencies:

- backend validation exception types
- UI-friendly label data

Prohibited responsibilities:

- no rule revalidation
- no backend-side error semantics changes
- no technical stack-trace rendering

#### `src/bnpl_cashflow/ui/screens.py`

Responsibility:

- render the individual wizard screens such as Welcome, Number of Credit Cards, Credit Card Names, Credit Card Details, BNPL Plan Entry, and Review
- collect user input through Streamlit widgets
- render controls and return user-entered values to `app.py`

Allowed dependencies:

- Streamlit
- `state.py` only where a very small shared helper is genuinely useful

Prohibited responsibilities:

- no navigation
- no session-state management
- no payload construction
- no backend invocation
- no validation
- no financial calculations

#### `src/bnpl_cashflow/ui/results.py`

Responsibility:

- render backend report-ready output in a clear Streamlit presentation
- improve grouping, headings, spacing, and visual hierarchy only where this remains a presentation concern
- rely on backend-provided result structures as the authoritative data source

Allowed dependencies:

- existing reporting output structures
- `streamlit` rendering helpers

Prohibited responsibilities:

- no calculation of totals or schedules
- no recomputation of obligations or projections
- no new report-section design logic unsupported by the backend output

### Scope of the proposed structure

This structure remains intentionally small.

The implementation should avoid abstracting the UI into multiple layers that do not materially improve clarity, because the approved MVP 3 scope is local and pragmatic.

## 4. Application Entry Point

The Streamlit entry point should be a small top-level app file:

- `src/bnpl_cashflow/ui/app.py`

This app should remain responsible for:

- starting the Streamlit session
- dispatching the current step to the lightweight screen-rendering module
- coordinating navigation and session state
- collecting submitted inputs from the screens layer
- generating the JSON-compatible payload from session state
- invoking the existing backend boundary
- presenting results and managing the result lifecycle

### Local run command

The local execution command should be documented as a simple Streamlit launcher, for example:

```text
python -m streamlit run src/bnpl_cashflow/ui/app.py
```

Because the repository uses a `src` layout, the implementation should account for the appropriate import path configuration for local execution. The plan does not require introducing a new root-level launcher unless convenience requires it.

### Import approach

The UI should import the existing backend public functions rather than importing internals directly:

- input parsing / validation boundary from the existing input layer
- application-service orchestrator from the existing application layer
- report rendering from the existing reporting layer

The UI should not import rule functions or backend internals directly in a way that bypasses the approved service boundary.

### Avoiding Streamlit coupling

To avoid coupling backend modules to Streamlit:

- keep all Streamlit-specific objects within `ui/`
- keep backend data models independent of `st.*` objects
- use pure dictionary or dataclass mapping in the payload-building layer
- keep the payload builder independent of Streamlit if practical

No backend module should need to know that it is running inside Streamlit.

## 5. Wizard Navigation Strategy

The guided MVP 3 workflow should use the simplest navigation approach that still feels like a wizard.

### Core navigation rules

- represent the current step with a simple session-state variable such as `current_step`
- use next-step and previous-step transitions that update the visible screen
- show a visible progress indicator such as `Step 3 of 7` or a restrained labelled sequence such as `Cards → Details → Plans → Review`
- preserve the current session data while the user moves backward and forward within the active session
- require completion checks before movement to later steps where practical
- allow direct editing from Review by returning the user to the relevant preceding step
- after editing, invalidate the previously generated result so it is not treated as current

### Navigation expectations

- `Back` returns to the previous screen without clearing current data
- `Continue` advances only after minimal UI completion checks pass
- `Review my details` moves the user to the review summary
- `Generate my projection` triggers submission to the approved backend flow
- `Edit my details` returns the user to the appropriate step before regeneration
- `Start over` clears the active session and returns the user to the first user-facing step after confirmation

### No unnecessary routing complexity

The implementation should not introduce a custom router, a page-state framework, or a large navigation abstraction. A small step index plus state-driven screen rendering is sufficient for MVP 3.

## 6. Session-State Model

The UI session state should remain temporary and local to the active browser session only.

### Proposed conceptual state keys

#### `current_step`

- purpose: identifies the current wizard screen
- initial value: `0` or the welcome step
- changes: whenever the user moves backward or forward
- cleared: when the user resets the session

#### `card_count`

- purpose: tracks how many card records the user wants to configure
- initial value: `1`
- changes: when the user changes the card count on Screen 1
- cleared: on reset

#### `credit_cards`

- purpose: stores editable card records in session state
- initial value: an empty list or a placeholder list based on card count
- changes: when the user edits names or details on earlier steps
- cleared: on reset

#### `bnpl_plans`

- purpose: stores BNPL plan records currently visible in the UI
- initial value: one empty plan row
- changes: when the user adds, removes, or edits plan rows
- cleared: on reset

#### `stable_ids`

- purpose: stores stable internal IDs for cards and plans that are generated automatically by the UI
- initial value: empty mapping or initial ID counter
- changes: when new cards or plans are added
- cleared: on reset

#### `validation_errors`

- purpose: stores friendly UI error details returned from backend validation mapping
- initial value: empty mapping or empty list
- changes: on each submission attempt and after field-level fixes
- cleared: when the error is resolved or the session is reset

#### `generated_result`

- purpose: stores the most recent successful backend result currently shown to the user
- initial value: `None`
- changes: after a successful backend submission
- cleared: on reset or when the current payload changes and the result becomes stale

#### `result_payload_fingerprint`

- purpose: stores a deterministic fingerprint for the last submitted payload
- initial value: `None`
- changes: whenever a payload is submitted successfully
- cleared: when the session resets or the payload is changed

#### `result_is_current`

- purpose: indicates whether the latest UI-display result still matches the current input
- initial value: `False`
- changes: set to `True` after a successful generation; set to `False` or cleared when an input changes
- cleared: on reset

#### `edit_return_step`

- purpose: remembers where the user should return after selecting `Edit my details`
- initial value: `None`
- changes: when the user chooses a section to edit from Review or Results
- cleared: after returning to the target step or after reset

#### `reset_confirmed`

- purpose: tracks whether the user has explicitly confirmed a complete session reset
- initial value: `False`
- changes: when `Start over` is selected and confirmation is requested
- cleared: after reset completes or the user cancels

### State rules

- session state is temporary only
- state is preserved only while navigating within the active session
- refreshing the browser, restarting the application, or intentionally selecting `Start over` may clear the session
- MVP 3 does not provide recovery or persistence after the active session is cleared
- no browser storage, autosave, database, or file persistence is introduced

## 7. Stable Identity Strategy

Stable internal identity is required because user-facing names can change while the payload must remain structurally stable.

### Identity behavior

#### Card IDs

- card IDs are created automatically by the UI when the card list is expanded
- card IDs are not manually entered by the user
- card IDs are not shown to the user
- card IDs remain stable even if a card name is changed
- BNPL plans continue to reference the correct card through the stable internal card ID

#### Plan IDs

- plan IDs are created when a BNPL plan row is added
- plan IDs are not manually entered
- plan IDs are not displayed to the user

### Card-count changes

When the user changes the credit-card count:

- new card placeholders are created for the added count
- removed cards must not leave behind dangling references in the payload
- the UI should handle card removal carefully, especially if existing BNPL plans still reference the removed card
- the implementation should detect such references and either prompt the user to reassign or remove dependent plans before submission

### Stability guarantee

A rename of a user-facing card name must not break BNPL-plan references because the payload continues to reference the stable internal card ID.

### Implementation detail boundary

The flow document should not prescribe a UUID algorithm or library. That decision belongs in the implementation plan or code-level implementation details, not in the UX flow requirements.

## 8. Form and Screen Responsibilities

The UI should keep each screen focused on a narrow set of responsibilities.

### Welcome

Information displayed:

- product name
- brief description of the purpose
- local-session reassurance

Information collected:

- none required beyond initiating the flow

Session-state changes:

- initialize the step counter and clear any prior active-session state if the user intentionally restarts

Navigation:

- `Get started` moves to the card-count screen

Completion checks:

- the screen is simply an entry point, so the UI should not require complex validation here

Backend validation responsibilities:

- none at this stage

### Number of Credit Cards

Information displayed:

- the prompt for how many cards the user wants to track

Information collected:

- a positive integer card count

Session-state changes:

- set `card_count`
- generate placeholder card records

Navigation:

- `Continue` advances to the names screen

Completion checks:

- value must exist and be greater than zero

Backend validation responsibilities:

- none at this stage

### Credit Card Names

Information displayed:

- one name field per card

Information collected:

- human-readable card names

Session-state changes:

- update `credit_cards[*].name`
- keep stable card IDs unchanged

Navigation:

- `Continue` advances to the details screen

Completion checks:

- each visible card should have a non-empty name

Backend validation responsibilities:

- backend will validate the final contract shape and required fields, not the UI

### Credit Card Details

Information displayed:

- card name
- statement closing day
- payment due day
- current or existing balance

Information collected:

- integer day-of-month values from 1 to 31
- non-negative monetary balance

Session-state changes:

- update `credit_cards[*].statement_closing_day`
- update `credit_cards[*].payment_due_day`
- update `credit_cards[*].existing_balance`

Navigation:

- `Continue` advances to the BNPL-plan entry screen

Completion checks:

- required fields must be present
- day values must be valid integers in the approved range
- balance must be a positive or zero monetary value

Backend validation responsibilities:

- the backend will confirm contract-level validity and the approved model constraints

### BNPL Plan Entry

Information displayed:

- a first editable plan row or a card-like plan input container
- add/remove controls for plans

Information collected:

- provider name
- plan name
- purchase amount
- currency
- purchase date
- first installment date
- installment count
- installment frequency
- selected credit card

Session-state changes:

- add/remove plan rows
- update row contents in real time
- maintain stable plan IDs

Navigation:

- `Add another plan` adds another row while preserving existing entries
- `Remove plan` removes an existing row
- `Review my details` advances to the Review screen

Completion checks:

- at least one plan remains visible
- each visible row should have all required fields completed
- a credit-card selection must be available and valid

Backend validation responsibilities:

- the backend validates contract shape, references, supported currencies, and all approved business constraints

### Review

Information displayed:

- summary of cards and plans in readable card or panel layout
- per-card summary values
- per-plan summary values

Information collected:

- no new data entry on this screen

Session-state changes:

- no new calculation logic
- preserve the working session data and allow users to return to earlier steps

Navigation:

- `Edit` returns the user to the relevant earlier screen
- `Generate my projection` submits the current payload to the backend

Completion checks:

- the review screen is a final human-check screen before submission
- the UI should not independently calculate or re-derive report content here

Backend validation responsibilities:

- backend remains the final validator before calculation is executed

### Projection Generation

Information displayed:

- a single call-to-action that submits the assembled payload

Information collected:

- none beyond the current session state

Session-state changes:

- build the payload dictionary
- compute the payload fingerprint
- call the input validation and application-service boundary
- store successful result and mark it as current

Navigation:

- on success, display Results
- on validation failure, remain on the current screen or return to the relevant step with friendly feedback

Completion checks:

- payload must be structurally valid enough to be passed to the backend

Backend validation responsibilities:

- all final validation stays in backend input validation and the application service

### Results

Information displayed:

- report-ready output returned by the approved backend

Information collected:

- none

Session-state changes:

- store current successful backend output
- mark result stale if the user changes any input after generation

Navigation:

- `Edit my details` returns to the prior review or relevant editing step
- `Start over` clears the active session after confirmation

Completion checks:

- display only backend-supported result sections

Backend validation responsibilities:

- backend remains authoritative for the actual financial reporting content

## 9. UI-Level Completion Checks

The UI may perform only a narrow set of completion checks before navigation or submission.

### Allowed UI checks

- a required visible field is present and non-empty
- a card count is present
- a dropdown selection has been made where required
- a visible numeric input is present
- at least one BNPL plan row remains visible
- an item is selected for follow-up review or editing

### Explicitly prohibited UI checks

The UI must not independently recreate backend validation or calculation enforcement, including:

- duplicate-ID validation
- cross-reference validation
- money normalization rules
- supported-currency validation
- mixed-currency validation
- date-rule validation
- installment constraints
- statement-cycle calculations
- due-date calculations

These rules remain the property of the existing backend input and application layers.

## 10. Payload Construction

The UI should construct the existing JSON-compatible MV2 payload from the active session state.

### Payload-building workflow

1. Read the current session state.
2. Convert UI records into a JSON-compatible dictionary structure matching the approved contract.
3. Use stable internal IDs for card and plan references.
4. Preserve the user-visible names only as display values; the payload must use the contract fields and stable internal IDs.
5. Pass monetary values as money-safe values according to the contract.
6. Pass dates as contract-compatible date values.
7. Preserve supported enum values such as `BIWEEKLY`.
8. Return the payload to the backend through the approved public validation and application-service workflow.

### Contract mapping expectations

The payload builder should align with `docs/json-contract.md` by mapping:

- card name to `name`
- statement closing day to `statement_end_day`
- payment due day to `payment_due_day`
- existing balance to `existing_balance`
- BNPL plan fields to the contract's required plan shape
- selected card name or display choice to the stable internal `credit_card_id`

### Allowed payload behavior

- preserve contract shape
- use stable IDs
- carry through supported currency values
- show and submit friendly values such as `Every 2 weeks` while sending the approved backend enum value `BIWEEKLY`

### Prohibited payload behavior

The payload builder must not:

- validate business rules
- normalize values in a way that duplicates the input layer
- calculate installments
- calculate balances
- access Streamlit-specific runtime objects directly if a pure function can avoid it

### Preferred testability

The payload-construction layer should be designed as a pure or nearly-pure mapping function so it can be tested independently of Streamlit execution.

## 11. Backend Integration

The approved backend integration point is the existing public application service workflow that already accepts validated payloads and returns structured results.

### Intended integration flow

1. Build a JSON-compatible payload dictionary from session state.
2. Pass the payload to the existing input parser/validator.
3. If validation passes, pass the resulting validated payload to the existing application service.
4. Receive structured application results from the existing backend.
5. Pass that backend result into the existing reporting presentation layer or a Streamlit-specific wrapper that simply displays the authoritative content.

### Intended public entry point

The public existing entry point already exposed by the repository is the current application-service workflow already used by the CLI:

- `bnpl_cashflow.input.parse_json_payload`
- `bnpl_cashflow.application.run_application`
- `bnpl_cashflow.reporting.render_application_report`

This matches the actual repository public API surface currently exported through the `bnpl_cashflow.input`, `bnpl_cashflow.application`, and `bnpl_cashflow.reporting` packages.

### Why the UI should not bypass this path

The UI must not call parser, rule, aggregation, or reporting internals individually because that would duplicate architectural responsibility and weaken the backend boundary.

The backend already provides the approved orchestration sequence, and MVP 3 should reuse it.

### Compatibility decision

No new application-service layer is needed for MVP 3.

If the current public flow does not accept the UI's in-memory dictionary directly, the smallest safe compatibility change is a thin adapter at the UI boundary that converts the UI-state structure into the approved contract representation and then hands it to the existing validation and application-service path.

That adapter should not add new logic; it should only adapt the presentation-layer input to the backend contract. No new application-service layer is introduced.

## 12. Validation Error Mapping

To keep the UI friendly while preserving backend correctness, the UI should map backend validation messages to user-facing feedback.

### Mapping goals

- preserve backend meaning
- map contract paths to the right screen or section
- map plan or card indexes to readable names where practical
- show field-level feedback where practical
- show a concise review summary where helpful
- preserve entered data after a validation failure
- clear resolved errors when the user corrects them

### UI error presentation strategy

- keep the backend authoritative for determining whether input is valid
- present backend errors in plain-language UI text
- use card names and plan names where that improves clarity
- avoid exposing raw internal paths or technical stack traces to ordinary users
- keep the user on the relevant step if that provides the best comprehension

### Example behavior

When the backend rejects a field, the UI may present a message such as:

- `Enter a valid purchase amount for Radar.`

instead of exposing the raw contract path and internal issue text.

### Error-handling boundary

The mapping layer changes presentation only. It must never change the meaning of validation or create new validation rules.

## 13. Projection Generation and Stale Results

The UI submission lifecycle should be simple and deterministic.

### Submission lifecycle

1. Build the current payload from session state.
2. Submit the payload to the existing backend validation and application-service flow.
3. If backend validation fails, keep the session data intact and show friendly field feedback.
4. If backend execution succeeds, store the successful result in session state.
5. Render the result screen from the backend output.

### Duplicate submissions

Where practical, the UI should prevent accidental duplicate generation by:

- disabling or guarding the generate action while the call is in progress
- using a single, clear submit action
- avoiding redundant submissions after a successful current result is already shown

### Stale-result handling

The implementation should treat any edit after a successful generation as a stale-result event.

Recommended approach:

- compute a deterministic payload fingerprint from the current submitted payload
- compare the fingerprint to the last successful result fingerprint
- if the current paid payload differs from the last generated payload, mark results as stale or clear the current result immediately
- require the user to regenerate before the output is treated as current

This keeps the results screen honest and aligned with the latest entered data.

## 14. Results Rendering

The UI should render the approved backend's report-ready output, not define a new reporting model.

### Architectural stance

- the backend reporting output remains authoritative
- the UI may improve spacing, typography, grouping, headings, responsiveness, and visual hierarchy
- the UI may choose a simpler card-based or panel-based layout for readability
- the UI must not independently create totals, projections, schedules, balances, or statement mappings
- the UI must not introduce report sections unsupported by the backend

### What the UI may present

The UI may render sections already produced by the approved backend output, for example:

- existing backend-supported installment projections
- cash-flow obligations
- card balance or existing-balance sections already returned by the backend

The UI should use human-readable card and plan names where the backend output already supports them.

### What the UI must not do

The UI must not:

- invent a new financial grouping model
- derive statement impacts independently from the backend result
- create projected balances that the backend does not already provide
- create new schedule sections not present in the approved backend report

### Empty-state rule

If the backend result is empty but successful, the UI should render a valid empty state rather than a misleading or broken screen.

## 15. Unexpected Error Handling

Unexpected runtime failures should be handled safely.

### Required user behavior

Normal users should not see:

- stack traces
- internal file paths
- raw exceptions
- source code snippets
- internal IDs

### Development behavior

The implementation may still log technical details for development purposes, but the user-facing message should remain generic and action-oriented.

Example user-facing message:

`Something went wrong while generating your projection. Please review your details and try again.`

### Recoverability

Entered session data should remain available after a recoverable failure so the user can review inputs and try again without starting over.

## 16. Reset and Edit Behaviour

The UI must support simple, safe editing and reset actions.

### `Edit my details`

- returns the user to the appropriate step or Review screen
- preserves unaffected state
- allows the user to correct entry errors or update selected values

### Section-specific edit actions from Review

- every review section should allow direct return to the earlier input step that owns that information
- edits should only modify the relevant local state, not reset unrelated information unless a broader reset is explicitly requested

### Returning to Review

After editing and before generation, users should be returned to Review so they can confirm updated values before resubmitting.

### Invalidating results after change

Any modification of input after a successful result has been generated should invalidate the current displayed result.

The UI should not treat older results as current after inputs have changed, even if the user navigates back to the results screen for review.

### `Start over`

- should intentionally clear the active session state
- should show confirmation before clearing meaningful entered data
- should return the user to the welcome or first configured screen after reset

### Reset scope

Reset behaviour should be limited to the current active local session. No persistence or recovery mechanism should be introduced.

## 17. Styling and Accessibility Approach

The styling and accessibility approach should be restrained and implementation-oriented.

### Visual principles

The implementation should follow `docs/ui-design-principles.md` by:

- using readable labels and text
- keeping information density moderate
- using card or panel grouping for forms
- showing a visible progress indicator
- keeping one primary action per screen
- supporting a clear focus order
- using keyboard navigation where Streamlit permits
- maintaining sufficient contrast
- avoiding dependence on colour alone

### Layout expectations

- laptop-first responsive behaviour
- no unnecessary horizontal density
- lightweight local presentation only
- minimal custom CSS unless the streamlit framework or workspace already requires a small amount of styling support

The implementation should avoid introducing a large design system or a custom frontend framework.

## 18. Testing Strategy

The implementation should use a layered testing approach.

### Pure unit tests

Recommended unit-test focus:

- payload construction from session data
- ID-preserving state transformations
- stale-result detection and fingerprint behavior
- validation-error mapping
- add/remove plan logic
- card-count change logic

These unit tests should verify control-flow boundaries rather than recreating backend calculation logic.

### Integration tests

Recommended integration-test focus:

- UI payload through the existing backend application service
- valid UI-generated payload producing the expected backend report-ready output
- invalid UI-generated payload preserving backend validation behavior
- CLI and UI using the same backend workflow

### Streamlit/UI tests

The UI test layer should verify:

- initial screen rendering
- navigation between steps
- preservation of session data while moving within the active session
- adding and removing plans
- editing values and returning to Review
- validation display and friendly feedback
- successful generation and result display
- stale-result behavior after changes
- reset behaviour

The project should use the existing supported Streamlit and Python test approach already available in the repository rather than introducing a new browser-test stack.

### Manual acceptance tests

Use a small number of real-world scenarios already validated in MVP 2 acceptance testing, focusing on the UI-driven workflow rather than re-testing every business-rule scenario.

The UI tests should verify orchestration and presentation boundaries, not duplicate the entire backend rule suite.

## 19. Implementation Phases

The implementation should be split into small, ordered phases.

### Phase 1: UI foundation and entry point

Objective:

- establish the local Streamlit entry point and the minimal package structure

Files expected to change:

- `src/bnpl_cashflow/ui/app.py`
- `src/bnpl_cashflow/ui/__init__.py`

Implementation tasks:

- create the entry point
- define the initial application shell
- confirm the import path and local execution flow

Automated tests:

- smoke test that the app initializes to the expected initial screen

Manual checks:

- the app launches locally
- the welcome screen is visible and usable

Completion criteria:

- the user can launch the Streamlit app locally

Review gate:

- verify the entry point and import path are aligned with the repository layout

### Phase 2: Session state and navigation

Objective:

- establish active-session state and step movement

Files expected to change:

- `src/bnpl_cashflow/ui/state.py`
- `src/bnpl_cashflow/ui/app.py`

Implementation tasks:

- define session-state keys
- implement step progression logic
- implement Back and Continue navigation
- implement reset confirmation and reset behavior

Automated tests:

- step transition tests
- state preservation tests
- reset flow tests

Manual checks:

- navigation remains stable while the user moves between steps
- the active session persists during navigation only

Completion criteria:

- step navigation and state handling are predictable and reviewable

Review gate:

- verify that step state is stored only in the active session and not persisted elsewhere

### Phase 3: Credit card workflow

Objective:

- implement the card-count, names, and card-details screens

Files expected to change:

- `src/bnpl_cashflow/ui/app.py`
- `src/bnpl_cashflow/ui/state.py`

Implementation tasks:

- wire card-count entry to state
- create card placeholders
- collect card names and details
- keep stable card IDs separate from display names

Automated tests:

- card-count updates
- names and details preservation
- stable ID survival during rename-like UI changes

Manual checks:

- the card workflow remains friendly and readable
- one card panel per credit card remains easy to use

Completion criteria:

- the credit-card workflow behaves like the approved UX plan

Review gate:

- verify the UI is only collecting the approved contract shape and does not add new logic

### Phase 4: BNPL plan workflow

Objective:

- implement the BNPL plan entry screen and plan add/remove behavior

Files expected to change:

- `src/bnpl_cashflow/ui/app.py`
- `src/bnpl_cashflow/ui/state.py`
- `src/bnpl_cashflow/ui/payload_builder.py`

Implementation tasks:

- add the first plan row by default
- support add/remove of plan rows
- preserve other rows while editing one plan
- maintain stable plan IDs hidden from users

Automated tests:

- add/remove row tests
- state-mutation tests
- plan row preservation tests

Manual checks:

- plan rows can be added and removed cleanly
- at least one plan remains available during supported flows

Completion criteria:

- the BNPL plan entry flow is stable and reviewable

Review gate:

- verify that add/remove behaviour preserves internal references correctly

### Phase 5: Review and payload construction

Objective:

- assemble the review screen and pure payload-construction logic

Files expected to change:

- `src/bnpl_cashflow/ui/payload_builder.py`
- `src/bnpl_cashflow/ui/app.py`

Implementation tasks:

- map session state to the approved JSON contract shape
- structure the review summary
- confirm direct editing from Review
- prepare the backend submission payload

Automated tests:

- payload-construction unit tests
- review navigation tests
- contract-shape tests

Manual checks:

- the review screen accurately reflects the collected data
- the payload matches the approved JSON contract shape

Completion criteria:

- the payload builder is independent of backend rule logic and is testable

Review gate:

- verify that the payload builder does not perform financial calculations or duplicate backend normalization

### Phase 6: Backend integration and validation mapping

Objective:

- connect the UI to the approved MVP 2 public workflow and map errors appropriately

Files expected to change:

- `src/bnpl_cashflow/ui/app.py`
- `src/bnpl_cashflow/ui/error_mapping.py`
- `src/bnpl_cashflow/ui/payload_builder.py`

Implementation tasks:

- call the existing input parser and application service from the UI
- map backend validation issues into friendly messages
- keep the user session intact after a validation failure
- preserve the backend decision on validity

Automated tests:

- integration tests using valid and invalid payloads
- validation-mapping unit tests

Manual checks:

- friendly feedback appears on the correct screen
- the UI does not show raw backend exception details to users

Completion criteria:

- the UI reuses the approved backend validation path and keeps the backend authoritative

Review gate:

- confirm the UI is not bypassing backend validation or duplicating rule enforcement

### Phase 7: Results rendering

Objective:

- present backend report-ready output in a readable Streamlit view

Files expected to change:

- `src/bnpl_cashflow/ui/results.py`
- `src/bnpl_cashflow/ui/app.py`

Implementation tasks:

- display backend-generated report-ready output
- improve readability using layout, typography, and grouping only
- keep backend output authoritative

Automated tests:

- results-screen rendering tests with known backend output

Manual checks:

- the display remains readable on a typical laptop screen
- the UI does not invent new report sections or recompute financial totals

Completion criteria:

- results are rendered from approved backend output only

Review gate:

- verify the UI is presenting existing backend information instead of creating a new reporting model

### Phase 8: Editing, stale-result handling, and reset

Objective:

- make the flow safe for iterative editing and regeneration

Files expected to change:

- `src/bnpl_cashflow/ui/state.py`
- `src/bnpl_cashflow/ui/app.py`

Implementation tasks:

- invalidate stale results after edits
- maintain edit-return destination
- support section-level edits from Review
- implement `Start over` with confirmation

Automated tests:

- stale-result detection tests
- reset and edit-return tests

Manual checks:

- a result is clearly marked as stale or cleared after a change
- users understand that regeneration is required

Completion criteria:

- editing does not silently reuse outdated results

Review gate:

- verify that stale-result rules remain simple and deterministic

### Phase 9: Styling, accessibility, and UX polish

Objective:

- carry the UI through the approved usability and accessibility principles

Files expected to change:

- `src/bnpl_cashflow/ui/app.py`
- `src/bnpl_cashflow/ui/results.py`

Implementation tasks:

- refine layout hierarchy
- improve label clarity and spacing
- ensure one primary action per screen
- preserve keyboard usability and focus order where Streamlit permits

Automated tests:

- regression tests for stale state and navigation

Manual checks:

- visible progress remains clear
- the UI remains calm, readable, and non-dense

Completion criteria:

- the UX remains aligned with the approved principles without adding extra product scope

Review gate:

- verify the UI is lightweight and approachable rather than technically ornate

### Phase 10: Full testing and acceptance review

Objective:

- confirm the complete MVP 3 workflow and the backend boundary are both stable

Files expected to change:

- tests only where needed for the UI work

Implementation tasks:

- run the relevant UI tests
- run the complete backend suite where appropriate
- review acceptance scenarios manually
- finalize documentation alignment

Automated tests:

- full project test suite if required for regression confidence

Manual checks:

- real-world scenario walkthroughs remain consistent with accepted MVP 2 behavior

Completion criteria:

- the full guided workflow works end-to-end without altering backend business logic

Review gate:

- confirm that all backend tests remain passing and no new scope has been introduced

## 20. Review and Commit Strategy

The implementation should be reviewed in phases rather than as one large batch.

At the end of each phase:

1. run the relevant automated tests
2. run the complete existing test suite where appropriate
3. conduct a human review against the approved docs
4. compare behavior against the documented architectural boundaries
5. confirm no backend rules or reporting logic were duplicated
6. commit the completed phase before moving to the next one

Recommended commit style:

- `ui: add streamlit entry point`
- `ui: add session state and navigator`
- `ui: implement card workflow`
- `ui: implement BNPL plan workflow`
- `ui: add review and payload builder`
- `ui: wire backend integration and error mapping`
- `ui: render approved results screen`
- `ui: add stale-result and reset behaviour`
- `ui: polish accessibility and review flow`

The next phase should not begin until the current phase passes its review gate.

## 21. Definition of Done

MVP 3 implementation is complete only when all of the following are true:

- the full guided workflow works
- user input is preserved during active-session navigation
- users never edit JSON manually
- payloads follow the approved JSON contract
- the UI calls the approved application-service boundary
- backend validation remains authoritative
- backend-generated results are displayed correctly
- no financial calculations are implemented in the UI
- no reporting logic is duplicated
- card and plan IDs remain stable
- add/remove behaviour works safely
- editing invalidates stale results
- reset behaviour works
- expected errors are friendly and actionable
- unexpected errors are safely handled
- existing CLI behaviour remains unchanged
- all existing backend tests pass
- all new UI tests pass
- real-world acceptance scenarios pass
- no out-of-scope feature is introduced
- all planning documents remain aligned with the implementation

## 22. Risks and Mitigations

### Risk: Streamlit rerun behaviour changes state unexpectedly

Mitigation:

- keep state in a small, explicit session-state model
- avoid fragile widget-key assumptions
- treat reruns as a normal part of the UI lifecycle, not as a data loss event

### Risk: inconsistent session-state mutation

Mitigation:

- centralize session-state helpers in `state.py`
- use one consistent data model for cards and plans
- keep updates predictable and reviewable

### Risk: unstable widget keys cause item confusion

Mitigation:

- use stable internal IDs for generated widgets and data records
- keep display names separate from internal identity
- validate that adding/removing rows does not reorder or misbind data incorrectly

### Risk: changing the card count causes data loss or broken references

Mitigation:

- preserve stable internal IDs
- detect plan references to removed cards
- require reassigning or removing dependent plans before submission

### Risk: duplicated validation in the UI

Mitigation:

- keep all final validation in the approved backend input layer
- limit the UI to completion checks only
- treat the backend as the only validation authority

### Risk: UI becomes coupled to backend internals

Mitigation:

- import only the public input/application/reporting entry points already approved by the backend design
- avoid reaching into rule functions or helper internals directly

### Risk: stale results are shown after editing

Mitigation:

- store a payload fingerprint
- invalidate or clear results whenever the payload changes
- require regeneration before the result is considered current

### Risk: error-path mapping becomes brittle

Mitigation:

- keep the mapping layer narrow and presentation-only
- map backend meaning to friendly UI labels rather than trying to re-serialize all backend metadata

### Risk: overuse of custom CSS or layout complexity

Mitigation:

- keep styling minimal and restrained
- use simple card or panel layout patterns
- prefer readability and clarity over decorative structure

### Risk: UI tests become tightly coupled to layout

Mitigation:

- test session behavior and payload flow first
- treat visual layout assertions as secondary and limited
- keep the test suite focused on orchestration and result correctness

## 23. Explicitly Deferred Work

The following work is intentionally deferred beyond MVP 3:

- persistence
- user accounts
- authentication
- cloud deployment
- APIs
- bank integrations
- saved plans
- payment tracking
- notifications
- imports
- exports
- currency conversion
- mobile-native application
- financial advice
- AI features

These features are out of scope and are not part of the MVP 3 implementation plan.
