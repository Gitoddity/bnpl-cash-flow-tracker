"""Structured projection reporting over the existing application pipeline.

Saved cards do not have a currency. Their entered balances therefore remain in
a separate, explicitly unspecified bucket; a plan's currency cannot label them.
"""
from datetime import date
from decimal import Decimal

from bnpl_cashflow.application.services import ApplicationService
from bnpl_cashflow.input.validation import validate_profile_payload


def build_projection(document: dict, as_of: date, start: date | None = None,
                     months: int = 6, card_id: str | None = None,
                     currency: str | None = None) -> dict:
    start = (start or as_of).replace(day=1)
    if not 1 <= months <= 24:
        raise ValueError("Choose between 1 and 24 months.")
    if start.year > 9996:
        raise ValueError("Choose a start year before 9997.")
    all_cards = document["credit_cards"]
    if card_id and not any(card["id"] == card_id for card in all_cards):
        raise ValueError("Choose a card from the active profile.")
    cards = [card for card in all_cards if not card_id or card["id"] == card_id]
    plans = [plan for plan in document["bnpl_plans"] if any(card["id"] == plan["credit_card_id"] for card in cards)]
    currencies = sorted({plan["currency"] for plan in document["bnpl_plans"]})
    if currency and currency not in [*currencies, "UNSPECIFIED"]:
        raise ValueError("Choose a currency from the active profile.")
    periods = [_month_after(start, offset) for offset in range(months)]
    end = _month_after(start, months)
    service = ApplicationService(lambda: as_of)
    charges, dues = [], []
    # The existing engine deliberately rejects mixed currencies in a group.
    # Run one currency at a time, without duplicating balances between runs.
    for code in currencies:
        if currency and currency != code:
            continue
        selected_plans = [plan for plan in plans if plan["currency"] == code]
        result = service.run(validate_profile_payload({
            "credit_cards": [{**card, "current_balance": "0.00"} for card in cards],
            "bnpl_plans": selected_plans,
        }))
        for plan_result in result.plan_results:
            for projection in plan_result.projections:
                charges.append({
                    "plan_id": plan_result.plan.id, "plan_name": projection.plan_name,
                    "provider_name": projection.provider_name,
                    "card_id": plan_result.credit_card.id, "card_name": projection.credit_card_name,
                    "installment_number": projection.installment_number,
                    "charge_date": projection.installment_date.isoformat(),
                    "statement_start": projection.statement_cycle_start_date.isoformat(),
                    "statement_close": projection.statement_cycle_end_date.isoformat(),
                    "due_date": projection.cash_flow_due_date.isoformat(),
                    "currency": code, "amount": format(projection.installment_amount, ".2f"),
                })
        dues.extend(_dues(result, code))
    if not currency or currency == "UNSPECIFIED":
        balance_result = service.run(validate_profile_payload({"credit_cards": cards, "bnpl_plans": []}))
        dues.extend(_dues(balance_result, "UNSPECIFIED"))
    charges = sorted((item for item in charges if start.isoformat() <= item["charge_date"] < end.isoformat()),
                     key=lambda item: (item["charge_date"], item["card_id"], item["plan_id"], item["installment_number"]))
    dues = sorted((item for item in dues if start.isoformat() <= item["due_date"] < end.isoformat()),
                  key=lambda item: (item["due_date"], item["card_id"], item["currency"]))
    monthly = []
    for period in periods:
        key = period.strftime("%Y-%m")
        monthly.append({"period": key,
                        "charges": _totals(item for item in charges if item["charge_date"].startswith(key)),
                        "dues": _totals(item for item in dues if item["due_date"].startswith(key))})
    next_due = next((item["due_date"] for item in dues if item["due_date"] >= as_of.isoformat()), None)
    return {"as_of_date": as_of.isoformat(), "start_date": start.isoformat(),
            "end_date": end.isoformat(), "months": months,
            "card_count": len(all_cards), "plan_count": len(document["bnpl_plans"]),
            "cards": [{"id": card["id"], "name": card["name"]} for card in all_cards],
            "currencies": currencies,
            "summary": {"charge_totals": _totals(charges), "due_totals": _totals(dues),
                        "next_due": {"date": next_due, "amounts": _totals(item for item in dues if item["due_date"] == next_due)} if next_due else None},
            "monthly": monthly, "charges": charges, "dues": dues}


def _month_after(start: date, offset: int) -> date:
    index = start.year * 12 + start.month - 1 + offset
    return date(index // 12, index % 12 + 1, 1)


def _totals(rows) -> list[dict]:
    totals: dict[str, Decimal] = {}
    for row in rows:
        totals[row["currency"]] = totals.get(row["currency"], Decimal("0.00")) + Decimal(row["amount"])
    return [{"currency": code, "amount": format(amount, ".2f")} for code, amount in sorted(totals.items())]


def _dues(result, currency: str) -> list[dict]:
    names = {card.id: card.name for card in result.credit_cards}
    plans = {plan.id: plan for plan in result.bnpl_plans}
    return [{"card_id": item.credit_card_id, "card_name": names[item.credit_card_id],
             "statement_start": item.statement_cycle_start_date.isoformat(),
             "statement_close": item.statement_cycle_end_date.isoformat(),
             "due_date": item.due_date.isoformat(), "currency": currency,
             "amount": format(item.total_amount, ".2f"),
             "balance_amount": format(item.current_balance_amount, ".2f"),
             "installment_count": len(item.installments),
             "plan_count": len({installment.plan_id for installment in item.installments}),
             "contributing_total": format(item.total_amount - item.current_balance_amount, ".2f"),
             "installments": [{
                 "plan_id": installment.plan_id,
                 "plan_name": plans[installment.plan_id].plan_name,
                 "provider_name": plans[installment.plan_id].provider_name,
                 "installment_number": installment.installment_number,
                 "installment_count": plans[installment.plan_id].installment_count,
                 "charge_date": installment.installment_date.isoformat(),
                 "amount": format(installment.installment_amount, ".2f"),
             } for installment in item.installments]} for item in result.cash_flow_obligations]
