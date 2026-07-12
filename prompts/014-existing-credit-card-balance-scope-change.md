# MVP 2 Existing Credit Card Balance Scope Change Review

User request:

MVP 2 scope change review: Existing Credit Card Balance.

Do not modify code yet.

Review and update the MVP 2 planning documents to include an explicit existing credit card balance input.

User requirement:
The user should be able to provide:

* existing credit card balance
* BNPL payment plans

The system should show how BNPL installments increment the card balance / future obligations.

Required documentation updates:

1. Update `docs/json-contract.md`
2. Update `docs/mvp2-scope.md`
3. Update `docs/mvp2-architecture.md`
4. Update `docs/mvp2-implementation-plan.md`

Acceptance criteria:

* Documentation explicitly defines `existing_balance`.
* Omitted `existing_balance` behavior is documented.
* Negative balances are rejected.
* Existing BNPL calculations are not changed.
* No interest, payment tracking, minimum payment, credit-limit, or reconciliation logic is added.
* No code changes are made in this documentation pass.

