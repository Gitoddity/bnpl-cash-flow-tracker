# Projection data interface

`GET /api/profiles/{profile_id}/projection` reads the saved profile on every
request and calculates through `ApplicationService`. It stores no results.

Optional query parameters:

- `start`: ISO date, normalized to the first of its month; default is the
  calculation date's month.
- `months`: 1–24, default 6. The response's `end_date` is exclusive.
- `card_id`: a card belonging to this profile.
- `currency`: a saved card or plan currency present in this profile, or
  `UNSPECIFIED` for older cards whose currency has not been set.

Amounts are decimal strings. `charges` describes provider installments charged
to cards, including the mapped statement start/close and card due date. `dues`
describes card obligations grouped by due date, card, and currency. The charge
and due windows are filtered independently: an installment charged before the
selected period may still contribute to a due inside it. Monthly and summary
totals are calculated in Python.

Cards support an optional saved `currency` field (CAD or USD). Add/Edit Card
provides an explicit selector; new cards start with a visible CAD selection.
Older profiles import without inventing a currency and can set it through Edit
Card, including the projection's Edit card currency action. Export preserves it.

The engine runs separately for each currency, including only the card balances
saved in that currency. Matching card dues combine a balance and installments
once. Different currencies remain separate without conversion. Legacy balances
with no currency run separately as `UNSPECIFIED` until the owner selects one.

The pipeline retains its existing date rules, paid-installment exclusion,
exact amount-paid adjustment, and rounding. Statement/due mapping for
installments can reject a nonexistent day in a short month; this must be shown
as a calculation error with retry, without substituting a new financial rule.
Current-balance date resolution uses the existing separate clamping behavior.
Projections are estimates based on entered information, not live balances,
bank connectivity, or automatic payments.

## Design retrieval status

On October 7, 2026, Stitch MCP `get_project`, `list_screens`, and `get_screen`
confirmed the current Cash Flow Projection screen remains
`8730f00740c648a29b85605644a8be5b` in project `6921387155947892246`.
The project update time was `2026-10-07T16:26:47.835153Z`.
The current HTML file is `13064866206879258504`, and screenshot file is
`3269709819073075761`. Both MCP-provided download URLs returned Google sign-in
HTML rather than assets. The supplied preview URL returned only the Stitch
application shell. The user subsequently supplied the updated screenshot,
which is the implementation's visual reference: month headings with separate
currency totals, dated card dues, payment-plan counts, expandable contribution
tables, and totals beneath each table. No chart appears in this revision.

## React screen

Both sidebar Projection and the Payment Plans Overview action open the screen.
The component is remounted on return from card/plan edits or additions and
fetches saved inputs again. Switching profiles retains the Projection route,
unmounts the prior profile's component, and ignores its outstanding request.
Refresh and period/card/currency filters request fresh backend calculations.

Contribution details are embedded in each due by Python, including provider,
plan, installment number/count and charge date, even if that charge occurred
before the selected period. Native disclosure controls provide keyboard
operation; tables scroll within their container on smaller screens.

The screenshot's "Minimum Payment" and "Statement Balance" labels require
financial data the app does not have. They are represented as "Projected card
due" or "Entered card balance due". Unsupported provider examples in the
mockup are not added; the app continues to use its saved supported providers.
DueMap branding and existing workspace navigation are retained. Projection's
sidebar profile actions reuse export, import, profile selection and creation.

Verification: 231 backend tests and 45 frontend tests pass, along with the
TypeScript check and Vite production build. Desktop (1544 px) and narrow
390 px content renders were inspected against the supplied screenshot using
synthetic profiles calculated by the Python pipeline. Local screenshots are
saved under `.local-data/projection-desktop.png` and
`.local-data/projection-mobile-final.png`; temporary frontend QA pages were
removed. The date labels, currency identifiers, estimate explanation and
existing DueMap top bar are intentional additions to the reference layout.
