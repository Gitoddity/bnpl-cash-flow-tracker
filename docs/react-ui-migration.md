# React UI migration — landing slice

Authorized 2026-09-24. React + TypeScript + Vite and FastAPI are added alongside
Streamlit. The existing domain, rules, application service, and CLI remain authoritative.
Stitch project `6921387155947892246`, screen `51bf3225a3b04966b5e38d6c3ff92445`
is the visual reference. DueMap is provisional branding configured in one frontend module.

## This slice

- Card correction is authorized: a pencil opens the existing form populated with
  saved values. PATCH updates only editable fields under the owning profile,
  preserving card IDs, plan references, and optional imported balance due dates.
  Existing Python validation applies; errors retain input and Cancel saves nothing.

- Prompt 018 expands the cards overview using Stitch `df4b497260154bc6a212b62a668a7522`
  and opens the plan form from `394c5bab3c614a038accd189cd42ba9c`. Upcoming dates are
  response-only fields, resolved from one server `as_of_date` per request using the
  existing application-service billing helpers. Closing today and payments due today
  count as upcoming. The next payment may correspond to the previous statement;
  it is not necessarily the payment for the next closing date. Existing end-of-month
  clamping and strict payment-after-close behavior are reused, not copied into React.
  Navigation scrolls to the top so transient save feedback is visible. Plan fields
  use real active-profile cards; unsupported monthly/interest modes are omitted.

- Responsive landing, dedicated Create Profile screen, import action, and active-profile empty state.
- Create Profile follows Stitch screen `36f0f225698343c98d37859d1704f40d`.
  Names are validated exclusively by FastAPI's existing profile operation. Errors
  stay beside the input without clearing it. Back returns to the unchanged landing.
  Hash routes identify the active profile, including after refresh. The empty state
  exposes Add Credit Card as the next-step entry point.
- FastAPI creates/lists/imports profiles; SQLite persists them on the server computer.
- Add Credit Card and persisted Cards Overview are authorized by prompt 017.
  Stitch references: `df771cad37d943d4a953784da7e501e8`,
  `c1b39fb32b544238bfeb5c7d59e82e6f` (corrected screen ID), and
  `df4b497260154bc6a212b62a668a7522`. Collect only nickname, decimal-string
  current balance, closing day, and due day. Python validates all financial inputs;
  the API converts integer day strings from the form without applying domain rules.
  Server-generated IDs and URL profile ownership prevent client ownership overrides.
  Append cards transactionally, preserving existing cards and plans. Read them from
  SQLite on refresh. Success notices are transient React state, dismissed after 4s.
- The user selected **Form and card selector only** for payment-plan entry. The
  Stitch details/card-selector screen is available, with a clear unsaved notice and
  disabled submission. No plan-saving endpoint, card editing, projection calculations,
  or export button yet. Projection navigation opens an explicitly unfinished screen.
- Future calculation endpoints must call parse_json_payload then run_application;
  TypeScript must not calculate installments, balances, statement cycles, or due dates.
- Share existing profile-name rules and financial input validators. Import permits
  empty profiles and cards without plans through a separate validator entry point;
  calculation payload requirements stay unchanged.
- Framework-independent profile functions live in `application/profiles.py`.
  `ui/profiles.py` re-exports them for Streamlit compatibility; the API never imports
  Streamlit or a UI module. This is a move of existing behavior, not a second implementation.
- Keep the Streamlit draft and its migration behavior untouched. The new store is
  `.local-data/profiles.sqlite3` (ignored), configurable by BNPL_PROFILE_DB.
- Local development only: bind to loopback, one server process, no authentication.
  No browser persistence, cloud sync, external fonts, analytics, or export claims.

## Portable profile contract v1

```json
{
  "format": "bnpl-profile",
  "version": 1,
  "profile": {"id": "personal-example", "name": "Personal"},
  "credit_cards": [],
  "bnpl_plans": []
}
```

One profile per document. Cards and plans use the existing JSON financial contract,
with canonical field names; each card must explicitly reference this profile's ID.
Reject unknown fields (including card-number fields), malformed JSON, unsupported
versions, invalid financial values, duplicate IDs, cross-profile ownership, broken
plan references, and files larger than 1 MiB. Money is represented as decimal strings.
Imported IDs are preserved within the profile. Duplicate profile ID or case-insensitive
name returns 409; never overwrite or merge. Writes are transactional.
Envelope limits: profile IDs are 1–128 characters without surrounding whitespace;
profile names are 1–120 characters and normalized by the shared profile function.

The old draft has multiple profiles, no version marker, and deliberately preserves
incomplete entries. It is not accepted as a portable profile. No automatic conversion
is performed. Export will later emit this same contract; it is not implemented now.

## Verification

Focused API tests cover creation, durable storage, collisions, import contracts,
financial validation reuse, reference integrity, and request limits. Frontend tests
cover create/import entry, success, failure, retry, and cancel. Run existing Python
regressions and the TypeScript production build. Visually review desktop/mobile.
