# Local browser development

Run commands from `C:\BNPL-Cash-Flow_Tracker`. Requires Python 3.10+ and Node.js
22.12+ (Node 24 LTS is suitable). Vite requirements: https://vite.dev/guide/.

## Install

```powershell
.\.venv\Scripts\python.exe -m pip install -e '.[api,test]'
cd frontend
npm.cmd ci
```

## Start API (terminal 1, repository root)

```powershell
.\.venv\Scripts\python.exe -m uvicorn bnpl_cashflow.api.app:app --reload --host 127.0.0.1 --port 8000
```

## Start browser frontend (terminal 2)

```powershell
cd C:\BNPL-Cash-Flow_Tracker\frontend
npm.cmd run dev
```

Open http://127.0.0.1:5173. Vite proxies `/api` to port 8000; no permissive CORS is
needed. Keep both servers bound to loopback. This slice has no authentication and
is not ready for shared/public hosting. API docs: http://127.0.0.1:8000/docs.

On this workstation Node is currently bundled with Codex rather than on PATH.
Until a standalone Node installation is available, prepend its folder in terminal 2:

```powershell
$env:Path = 'C:\Users\Srira\AppData\Local\OpenAI\Codex\runtimes\cua_node\426e88130fe66c7e\bin;' + $env:Path
```

That bundled path may change with Codex updates. The project has no dependency on
that particular path; any supported Node installation works.

## Behavior and data

- Create New Profile opens `#/profiles/new`, a dedicated Stitch-based screen. Create
  Profile submits the name to FastAPI, selects the saved profile, and navigates to
  `#/profiles/<id>`. Backend errors stay beside the input without clearing it.
  Back returns to the landing page without creating anything.
- Import Profile on either the landing or create screen selects a JSON file and submits its bytes to FastAPI.
  Try `examples/profile-v1.json`. Importing it again returns a conflict without replacement.
- Saved profiles can be selected from the landing page. The active profile URL can
  be refreshed to restore that profile from FastAPI. Empty profiles show Add Credit
  Card; clicking it opens `#/profiles/<id>/cards/new`. Save uses the active profile's
  FastAPI endpoint and returns to the persisted Cards Overview. Cancel saves nothing.
  Card editing, plan editing, calculation views, and JSON export remain future slices.
- Data lives in `.local-data/profiles.sqlite3` on the API computer. Set `BNPL_PROFILE_DB`
  before starting the API to choose another location. The file is ignored by Git.
- No browser localStorage, remote fonts, analytics, or cloud persistence. SQLite is
  local storage, not encrypted storage. The Streamlit draft is never read or changed.
- Card creation accepts only nickname, current balance, closing day, and due day.
  Credential fields, network, APR, credit limit, client IDs, and ownership overrides
  are rejected. Days are converted from integer text by the API, then validated by
  the existing Python rules (1–31, no closing/due ordering restriction). Balances
  stay decimal strings; React performs no money, date, or statement calculations.
- See `react-ui-migration.md` for the versioned portable profile contract.
- Brand name, tagline, and description live in `frontend/src/brand.ts`.

## Checks

Card correction: click the pencil at the top right of a saved card. The form opens
with its saved nickname, balance, closing day, and due day. Save Changes uses
`PATCH /api/profiles/{profile_id}/cards/{card_id}`; Python validates and returns the
updated card with refreshed schedule dates. IDs, imported explicit balance due dates,
and linked plans are preserved. Cancel makes no changes. Test an invalid day, correct
it, save, then refresh to verify persistence. The success message appears only after
the update and dismisses after four seconds.

```powershell
.\.venv\Scripts\python.exe -m pytest -q
cd frontend
npm.cmd test
npm.cmd run build
```

API tests use isolated temporary SQLite files. Frontend tests mock the HTTP adapter;
backend tests validate actual persistence and import behavior. FastAPI testing reference:
https://fastapi.tiangolo.com/tutorial/testing/.

### Create Profile manual check

1. Open http://127.0.0.1:5173 and choose Create New Profile.
2. Submit whitespace: confirm an inline error and retained input.
3. Enter a unique name and create: confirm the active profile name and Add Credit Card.
4. Refresh the profile URL: confirm the same profile is restored.
5. Back, create again with the same name: confirm rejection without replacement.
6. On the create screen, import `examples/profile-v1.json`; confirm profile navigation.
   A second import should report a conflict while retaining the typed name.
7. Review the create form at desktop and mobile widths. It uses a 448px maximum
   card width and responsive padding; automated browser visual review was unavailable
   in the implementation session because no browser was connected.

The existing Streamlit app remains available:

```powershell
.\.venv\Scripts\python.exe -m streamlit run src\bnpl_cashflow\ui\app.py
```

### Add Credit Card manual check

1. Create or open a profile. Choose Add Credit Card. Confirm the active workspace
   name, privacy panel, and exactly four inputs. Cancel returns without saving.
2. Submit a blank nickname, invalid balance, closing day 32, and due day 0. Confirm
   errors beside the fields, focus on the first error, and all entered values retained.
3. Enter `TD Visa`, `500.00`, closing day `18`, due day `12`. Save. Confirm the overview
   shows those values and a dismissible `TD Visa added successfully.` status.
4. Use Add Another Card within four seconds; confirm a fresh form. The persistent
   Add Credit Card button remains available after the notification disappears.
5. Save another card, refresh, and verify both cards remain without a success notice.
6. Open a different profile and confirm its card list is independent.
7. Check at 1440px desktop and 390px/320px mobile widths: sidebar becomes a compact
   workspace strip; billing inputs and buttons stack; card grid becomes one column;
   long nicknames wrap. Browser visual verification remains pending because no
   browser is connected in the implementation environment.

Card endpoints:

- `GET /api/profiles/{profile_id}/cards`: persisted cards for this profile; 404 if missing.
- `POST /api/profiles/{profile_id}/cards`: append one card, returning the canonical card
  with server ID and ownership (201). Body: `{ "name": "TD Visa", "current_balance":
  "500.00", "statement_end_day": "18", "payment_due_day": "12" }`. Numeric integer
  days also work. Omitting balance retains the existing backend zero default; an
  explicitly blank or invalid balance is rejected. Field errors return 422 with
  `issues[].path` / `message`; storage failures return 503 without changing form state.

SQLite locks the append transaction before reading, so concurrent saves preserve
every existing card and plan. No payment-plan/projection API is added in this slice.

### Updated overview and payment-plan entry

Both card endpoints now return three additional ISO date fields:
`as_of_date`, `next_statement_close_date`, and `next_payment_due_date`.
They are resolved using the application's server-local `date.today` clock (injectable
in tests) and existing Python application billing helpers, never financial logic in
React. Each response uses one as-of date. These fields are not stored or exported;
reopening the profile resolves them again. Dates today count as upcoming. The next
payment can belong to the previous statement cycle. For example, as of September
24, 2026, closing day 18 and due day 12 resolve to October 18 and October 12.
Short months use the existing application-service clamping behavior.

1. Save a card after scrolling down the form. Confirm navigation returns to the top
   with a success icon, the card nickname, close button, and Add Another Card.
2. Confirm the card appears immediately with full month/day/year schedule dates.
3. Wait four seconds: the notice disappears; Add Credit Card remains available.
4. Refresh or reopen: the cards persist and success does not repeat.
5. Choose Add Payment Plan beneath the cards (or Payment Plans in the navigation).
   The Stitch-based form lists only this profile's cards; selecting one shows its
   returned dates. As explicitly chosen for this step, the form does not save yet.
6. Cancel returns to the overview. Switch profiles and confirm selector isolation.
7. An empty profile keeps the first-card action and has no next-step panel. Projection
   navigation currently opens a coming-later message; no financial results are invented.

The overview uses a 280px desktop sidebar, responsive saved-card grid, horizontal
mobile navigation, and stacked mobile next-step/actions. Visual browser verification
still requires a connected browser; automated tests cover behavior, not rendered layout.
