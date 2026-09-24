# Edit credit cards — 2026-09-24

User request:

> if a user enters wrong information and wants to correct it they should be able to do so .
> Create a pencil icon on the top right corner of the credit card added and allow users to edit the informaiton

Implementation: accessible pencil on each card opens the existing form with saved
values. PATCH updates editable fields under the owning profile, preserves IDs and
plan references, and reuses Python validation. Cancel discards edits. Successful
saves replace the tile immediately and show a transient update notification.
Related: `frontend/src/CardsWorkspace.tsx`, `frontend/src/AddCardScreen.tsx`,
`src/bnpl_cashflow/api/profiles.py`, `docs/react-development.md`.
