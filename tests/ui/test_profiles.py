from __future__ import annotations

from datetime import date

from bnpl_cashflow.application import ApplicationService
from bnpl_cashflow.input import parse_json_payload
from bnpl_cashflow.ui.drafts import load_draft
from bnpl_cashflow.ui.profiles import cards_for_profile, create_profile, delete_profile, plans_for_profile, rename_profile


def _card(profile_id: str, card_id: str = "card_1") -> dict:
    return {"id": card_id, "name": "RBC", "profile_id": profile_id, "current_balance": "0.00", "statement_end_day": 10, "payment_due_day": 25}


def _plan(card_id: str = "card_1") -> dict:
    return {"id": "plan_1", "provider_name": "PayPal", "plan_name": "Laptop", "purchase_amount": "100.00", "currency": "CAD", "purchase_date": "2026-06-12", "first_installment_date": "2026-06-12", "installment_count": 1, "installment_frequency": "BIWEEKLY", "credit_card_id": card_id}


def test_profiles_have_stable_ids_and_empty_profiles_are_listable():
    profiles: list[dict[str, str]] = []
    personal, number = create_profile(profiles, 1, "Personal")
    empty, number = create_profile(profiles, number, "Empty")
    assert personal == {"id": "profile_1", "name": "Personal"}
    assert empty in profiles
    assert number == 3


def test_multiple_profile_isolation_rename_and_card_specific_results():
    profiles = [{"id": "profile_1", "name": "Personal"}, {"id": "profile_2", "name": "Household"}]
    cards = [_card("profile_1", "card_1"), {**_card("profile_2", "card_2"), "statement_end_day": 6, "payment_due_day": 27}]
    plans = [_plan("card_1"), {**_plan("card_2"), "id": "plan_2", "plan_name": "House"}]
    assert [card["id"] for card in cards_for_profile(cards, "profile_1")] == ["card_1"]
    assert [plan["id"] for plan in plans_for_profile(cards, plans, "profile_2")] == ["plan_2"]
    before = ApplicationService(today_provider=lambda: date(2026, 6, 1)).run(parse_json_payload({"credit_cards": [cards[0]], "bnpl_plans": [plans[0]]}))
    rename_profile(profiles, "profile_1", "Household Spending")
    after = ApplicationService(today_provider=lambda: date(2026, 6, 1)).run(parse_json_payload({"credit_cards": [cards[0]], "bnpl_plans": [plans[0]]}))
    assert profiles[0]["id"] == "profile_1"
    assert before == after
    both = ApplicationService(today_provider=lambda: date(2026, 6, 1)).run(parse_json_payload({"credit_cards": cards, "bnpl_plans": plans}))
    assert {item.payment_due_date for item in both.due_dates} == {date(2026, 7, 25), date(2026, 7, 27)}


def test_delete_active_profile_cascades_and_uses_first_remaining():
    profiles = [{"id": "profile_1", "name": "Personal"}, {"id": "profile_2", "name": "Household"}]
    profiles, cards, plans, active = delete_profile(profiles, [_card("profile_1")], [_plan()], "profile_1", "profile_1")
    assert profiles == [{"id": "profile_2", "name": "Household"}]
    assert cards == [] and plans == [] and active == "profile_2"
    profiles, cards, plans, active = delete_profile(profiles, cards, plans, active, "profile_2")
    assert profiles == [] and cards == [] and plans == [] and active is None


def test_legacy_draft_migrates_profile_names(tmp_path):
    path = tmp_path / "legacy.json"
    path.write_text('{"credit_cards":[{"id":"card_1","name":"RBC","profile_name":"Personal","current_balance":"0.00","statement_end_day":10,"payment_due_day":25}],"bnpl_plans":[{"id":"plan_1","provider_name":"PayPal","plan_name":"Laptop","purchase_amount":"100.00","currency":"CAD","purchase_date":"2026-06-12","first_installment_date":"2026-06-12","installment_count":1,"installment_frequency":"BIWEEKLY","credit_card_id":"card_1"}]}', encoding="utf-8")
    profiles, cards, plans = load_draft(path)
    assert profiles == [{"id": "profile_1", "name": "Personal"}]
    assert cards[0]["profile_id"] == "profile_1" and plans[0]["credit_card_id"] == "card_1"
