# Payment Plans Overview

Implemented on `feature/react-ui-enhancement`, using Stitch project
`6921387155947892246`, screen `c0c897610a4a402fa766bf4744158cee`.
The screen screenshot and HTML were retrieved through the configured Stitch
connection and inspected before implementation. Reference downloads are ignored
under `.local-data/stitch`.

The existing DueMap shell contains an active-profile selector and Export Profile
download link. Three compact summaries precede a semantic table. Provider and card
nickname have separate columns. Below 700px, rows become stacked, labeled cards;
all actions and progress information remain available. There are dedicated empty,
no-card, loading, and retry states. API failures never display zero summaries.

## Reporting and API

`application/plan_overview.py` builds reporting from the existing application
pipeline's outstanding installments, one plan at a time. It respects installment
rounding, paid counts, and exact `amount_paid` reconciliation. It never sums credit
card balances or uses card bill due dates for these summaries.

- Active Plans counts plans with at least one unpaid installment.
- Remaining Installments Total sums unpaid amounts separately by currency.
- Next Installment Charge uses the earliest unpaid installment date, combining
  amounts on that date separately by currency. An unpaid date in the past remains
  unpaid; the report does not silently skip it based on today's date.
- Completed plans remain visible with zero remaining count and amount.

`GET /api/profiles/{profile_id}/plans/overview` returns `plans` and `summary`.
Rows include persisted plan inputs plus `credit_card_name`,
`remaining_installment_count`, `remaining_amount`, `completed`, and
`progress_percent`. `summary` contains `active_plans`, `remaining_totals`
(`[{currency, amount}]`), and nullable `next_charge` (`{date, amounts}`). Monetary
values are decimal strings. These derived fields are never persisted or exported.

`PATCH /api/profiles/{profile_id}/plans/{plan_id}` accepts the editable plan fields
using the existing create schema. It preserves the plan ID and profile association,
and preserves exact `amount_paid` if omitted. ID/ownership overrides and foreign
cards are rejected. `DELETE` at the same path removes only that profile's plan.
Both operations lock before reading, preventing lost concurrent changes. Missing
plans return 404. Validation failures retain the stored plan.

The browser reuses the existing controlled form for editing and the existing
accessible success notification for create/update/delete. Delete uses a modal
confirmation naming the plan. Each mutation reloads the backend overview. The
API stores only inputs and has no projection-result cache; fresh pipeline runs
ensure a mutation cannot retain a stale projection. Notifications live only in
React state, expire after four seconds, and do not replay after refresh.

Version 1 portable profiles now permit CAD and USD plans together. Profile import,
storage validation, and overview reporting support this; no conversion occurs.
The legacy calculation payload validator retains its single-currency restriction.
Reporting runs each plan separately rather than passing mixed currencies into
the legacy aggregator. The existing export endpoint downloads only the active
profile and its cards/plans, using the established `bnpl-profile` version 1 shape.

## Verification and local review

Run `.venv\Scripts\python.exe -m pytest -q`; from `frontend`, run `npm.cmd test`
and `npm.cmd run build` with Node.js on PATH.

Focused checks cover rounding, shared next-charge dates, exact amount-paid
reconciliation, completed plans, mixed-currency export/import round trips,
profile isolation, identity-preserving edits, invalid edits, delete/cancel/retry,
notifications, scoped export links, and the existing add/cancel/add-another flow.

Start `Start-DueMap.bat` or the desktop shortcut and open
http://127.0.0.1:5173. Select a profile, then Payment Plans. Check populated fields
when editing, save, delete with confirmation, and refresh. Export the profile and
import it into a separate local database to test a round trip (the same database
correctly rejects duplicate profile IDs/names).

Desktop/mobile visual review remains pending: browser inventory returned no
connected browsers, and both in-app browser and Chrome creation were unavailable.
Review at 1440px, 1024px, 390px, and 320px. Confirm the compact summaries/table,
stacked mobile rows, wrapped long names, aligned amounts, and reachable actions.

Next task: implement the active profile's Cash Flow Projection screen. The
overview's View Cash Flow Projection button already opens its existing route;
this change retains the placeholder rather than building that screen.

## Purchase icons and provider logos

Add/Edit Payment Plan includes an optional icon picker with 12 purchase icons and
six colors, independent of the provider. Each plan can choose its own combination;
combinations can be reused. The overview displays that icon beside the purchase
name and a separate provider logo beside the provider's name. The selected
provider also appears with its logo inside the dropdown's selected value. Every
dropdown option contains its own provider logo and label. The selector supports
arrow keys, Home/End, first-letter navigation, Enter/Space selection, Escape,
Tab, and outside-click dismissal. Affirm's white asset uses a dark badge for
contrast in both the selector and overview.

Optional `icon` and `icon_color` fields are validated against fixed catalogs in
`application/plan_appearance.py` and persisted/exported as presentation metadata.
They never enter domain calculations. Omitted fields preserve existing appearance
on edit; legacy plans without fields display a slate shopping bag. Version 1
profiles without these fields continue to import unchanged. Unknown icon/color
values are rejected before writing, including during import.

Assets are bundled under `frontend/public/providers`. Sources and the Simple
Icons license are retained there. Provider names remain visible beside decorative
logos. The app makes no requests to remote logo services. Picker buttons have
accessible names, selected state, keyboard focus, and 44px minimum hit targets.
