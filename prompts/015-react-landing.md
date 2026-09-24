# React landing migration

Date: 2026-09-24

User request: Create feature/react-ui-enhancement from the current baseline and begin
the BNPL Cash Flow Tracker migration using React, TypeScript, Vite, and FastAPI.
Implement only Stitch landing screen 51bf3225a3b04966b5e38d6c3ff92445 in project
6921387155947892246. Keep provisional DueScope branding configurable. Inspect existing
profiles, drafts, boundaries, and tests first. Keep Streamlit working. Create New
Profile must enter the new-profile flow; Import Profile must accept JSON through
backend validation without overwriting existing profiles. Define a versioned contract
if drafts are unsuitable. Storage/privacy copy must be accurate; do not collect full
card numbers. Add focused tests, run checks, document local startup, and stop before
other screens. Preserve existing work; do not duplicate financial calculations.

Decisions: isolated local SQLite store; v1 single-profile import; shared Python
validation; minimal creation dialog rather than building a second full screen.
See docs/react-ui-migration.md and docs/react-development.md.

## Full user prompt

Create a feature branch and begin the BNPL Cash Flow Tracker UI enhancement. The chosen stack is **React + TypeScript + Vite** for the browser frontend and **FastAPI** for the backend. Keep the existing Python domain models and cash flow calculation pipeline as the source of truth.

Start with **the Landing / Empty State screen only**. Use the existing Stitch design as the visual reference; do not redesign the whole application or build the other screens yet. The Stitch project ID is `6921387155947892246`, and the Landing / Empty State screen ID is `51bf3225a3b04966b5e38d6c3ff92445`. The current screen says “DueScope”; keep that name provisionally and make it easy to change later.

Please work in this order:

1. Inspect the repository, its instructions, current branch, and `git status`. Preserve all existing uncommitted work. Create a branch named `feature/react-ui-enhancement` from the appropriate current baseline; do not discard, overwrite, or silently commit existing changes. Tell me if the branch name already exists or the working tree makes the branch choice ambiguous.
2. Inspect the existing profile and local draft behavior, application boundaries, and relevant tests. Briefly report how the new frontend will call FastAPI without duplicating financial calculations.
3. Scaffold the React + Vite frontend and the minimal FastAPI integration needed for this first screen. Keep the existing Streamlit app working during the migration.
4. Implement the landing page to match Stitch at desktop and mobile widths. Include **Create New Profile** and **Import Profile** actions. Make the actions functional: creating a profile should enter the new profile flow, and importing should accept a profile JSON file through a validated backend operation. Do not silently overwrite an existing profile. If the existing draft format cannot safely serve as a portable profile format, define a versioned profile export/import contract and explain the choice.
5. Make the storage and privacy copy accurate for the implementation. Do not claim that data is stored in the browser, disappears when the tab closes, or can be exported until those statements are true. Avoid collecting full credit card numbers.
6. Add only focused tests needed to verify the landing actions and JSON import validation. Run the relevant checks and show me how to start both development servers locally.

This branch will later include JSON export and editing credit cards and payment plans, so structure the new code with those flows in mind. For this step, stop after the landing page and its working actions. Summarize files changed, what works, what remains for the next screen, and any decisions I need to make.
