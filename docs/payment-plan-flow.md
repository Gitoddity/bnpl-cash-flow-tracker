# Add Payment Plan

Scope: implement the September 27, 2026 request on feature/react-ui-enhancement,
using Stitch project 6921387155947892246 screens 394c5bab3c614a038accd189cd42ba9c
and 3b5a1980095f4b8c8b0602532e94ea0d. Preserve profile and card flows.

Plans belong to the active profile through its stable card ID. Provider choices
are paypal, klarna, afterpay, sezzle, affirm; formatted legacy names normalize
on import. CAD and USD remain supported, with separate totals and no conversion.
Frequency remains BIWEEKLY. Python validates and generates installments before
transactional persistence. Calculated projections are not persisted or cached by
the React API; every calculation uses current saved inputs.

The reusable controlled form preserves values on errors, maps Python issues to
fields, focuses the first invalid field, and prevents duplicate submissions.
No-card profiles receive Add Credit Card guidance. Cancel returns to the entry
screen. Saving opens the plan overview with an immediate saved result and an
ephemeral, dismissible four-second status notification with Add Another Plan.


## Local verification

From the repository root, start the API:

```powershell
.\.venv\Scripts\python.exe -m uvicorn bnpl_cashflow.api.app:app --reload --host 127.0.0.1 --port 8000
```

In another terminal, run `cd frontend` then `npm.cmd run dev`. Open
http://127.0.0.1:5173. Select a profile with a card and use Add Payment Plan below
the cards. Also try Payment Plans in the sidebar and its empty-state/add button.

1. Confirm no provider is initially selected; select any of the five choices.
2. Submit empty/invalid fields, including paid count greater than total. Confirm
   inline errors, focus, and preservation of every value and provider selection.
3. Save Laptop / PayPal / a card / CAD 100.01 / September 1, 2026 purchase /
   September 2 first installment / 4 total / 1 paid. The overview shows 3 remaining.
4. Confirm the once-only success notice, close button, Add Another Plan, and
   four-second dismissal. Refresh: the plan remains and the notice does not recur.
5. Cancel from both entry screens; confirm the active profile stays selected.
6. Try a profile with no cards: Add Payment Plan shows Add Credit Card guidance.
7. GET `/api/profiles/{id}/export`, then import into a separate local store to
   verify round-trip persistence (same-store duplicate profiles are rejected).
8. Check at desktop and mobile widths: single-column mobile fields and sticky
   actions. Visual QA still needs a connected browser; none was available here.

Checks: `python -m pytest -q`; in frontend, `npm.cmd test` and `npm.cmd run build`.
The calculation rules and application service are unchanged by this feature.
There is no calculated-projection cache in this React/API stack to invalidate;
only current inputs are persisted, and the pipeline runs before each plan save.

Edit reuse: supply `initialValues` (counts represented as input strings),
`submitAction`, `submitLabel`, and `title` to AddPaymentPlanScreen. Provider and
card identifiers and all schedule values are controlled from those initial values.

The compact overview, edit/delete actions, mixed-currency profile support, and
header export action are now implemented. See [Payment Plans Overview](payment-plans-overview.md).
