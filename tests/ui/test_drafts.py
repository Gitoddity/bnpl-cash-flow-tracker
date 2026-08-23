from __future__ import annotations

from pathlib import Path

from bnpl_cashflow.ui.drafts import discard_draft, draft_exists, load_draft, save_draft


def test_draft_round_trip(tmp_path: Path):
    draft_path = tmp_path / "draft.json"
    cards = [
        {
            "id": "card_1",
            "name": "Tangerine",
            "current_balance": "102.00",
            "statement_end_day": 13,
            "payment_due_day": 13,
        }
    ]
    plans = [
        {
            "id": "plan_1",
            "provider_name": "PayPal",
            "plan_name": "Coffee",
            "purchase_amount": "100.00",
            "currency": "CAD",
            "purchase_date": "2026-07-01",
            "first_installment_date": "2026-07-01",
            "installment_count": 4,
            "paid_installment_count": 1,
            "amount_paid": "25.00",
            "installment_frequency": "BIWEEKLY",
            "credit_card_id": "card_1",
        }
    ]

    saved_path = save_draft(cards, plans, draft_path)

    assert saved_path == draft_path
    assert draft_exists(draft_path)
    assert load_draft(draft_path) == (cards, plans)

    discard_draft(draft_path)
    assert not draft_exists(draft_path)
