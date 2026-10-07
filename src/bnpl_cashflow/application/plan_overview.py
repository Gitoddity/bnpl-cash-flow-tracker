"""Provider-charge reporting from the same outstanding schedules as projections."""
from decimal import Decimal

from bnpl_cashflow.application.services import run_application
from bnpl_cashflow.input.validation import validate_profile_payload


def build_plan_overview(document: dict) -> dict:
    rows = []
    totals: dict[str, Decimal] = {}
    charges: dict = {}
    active = 0
    for saved in document["bnpl_plans"]:
        # Run each plan independently: never aggregate currencies in the engine.
        result = run_application(validate_profile_payload({
            "credit_cards": document["credit_cards"], "bnpl_plans": [saved],
        })).plan_results[0]
        remaining = sum((item.installment_amount for item in result.installments), Decimal("0.00"))
        count = len(result.installments)
        active += bool(count)
        currency = result.plan.currency
        totals[currency] = totals.get(currency, Decimal("0.00")) + remaining
        for installment in result.installments:
            by_currency = charges.setdefault(installment.installment_date, {})
            by_currency[currency] = by_currency.get(currency, Decimal("0.00")) + installment.installment_amount
        rows.append({**saved, "credit_card_name": result.credit_card.name,
                     "remaining_installment_count": count, "completed": count == 0,
                     "remaining_amount": format(remaining, ".2f"),
                     "progress_percent": result.plan.paid_installment_count * 100 / result.plan.installment_count})

    def amounts(values: dict) -> list[dict]:
        return [{"currency": currency, "amount": format(amount, ".2f")} for currency, amount in sorted(values.items())]

    next_date = min(charges) if charges else None
    return {"plans": rows, "summary": {
        "active_plans": active, "remaining_totals": amounts(totals),
        "next_charge": {"date": next_date.isoformat(), "amounts": amounts(charges[next_date])} if next_date else None,
    }}
