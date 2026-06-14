from __future__ import annotations

from collections import OrderedDict
from datetime import date
from decimal import Decimal
from typing import Sequence

from bnpl_cashflow.domain import CashFlowObligation, DueDate, Installment


def aggregate_cash_flow(installments: Sequence[Installment], due_dates: Sequence[DueDate]) -> list[CashFlowObligation]:
    if len(installments) != len(due_dates):
        raise ValueError("installments and due_dates must have the same length")

    grouped: OrderedDict[tuple[str, date], dict[str, object]] = OrderedDict()

    for installment, due_date in zip(installments, due_dates):
        if not isinstance(installment, Installment):
            raise TypeError("installments must contain Installment instances")
        if not isinstance(due_date, DueDate):
            raise TypeError("due_dates must contain DueDate instances")
        if installment.credit_card_id != due_date.credit_card_id:
            raise ValueError("installment credit_card_id must match due_date credit_card_id")

        key = (installment.credit_card_id, due_date.payment_due_date)
        bucket = grouped.get(key)
        if bucket is None:
            bucket = {
                "statement_cycle_end_date": due_date.statement_cycle_end_date,
                "currency": installment.currency,
                "installments": [],
                "total_amount": Decimal("0.00"),
            }
            grouped[key] = bucket

        if bucket["statement_cycle_end_date"] != due_date.statement_cycle_end_date:
            raise ValueError("all installments in a cash flow group must share the same statement cycle end date")
        if bucket["currency"] != installment.currency:
            raise ValueError("all installments in a cash flow group must use the same currency")

        bucket["installments"].append(installment)  # type: ignore[union-attr]
        bucket["total_amount"] = bucket["total_amount"] + installment.installment_amount  # type: ignore[operator]

    obligations: list[CashFlowObligation] = []
    for (credit_card_id, payment_due_date), bucket in sorted(grouped.items(), key=_sort_key):
        installments_for_group = tuple(bucket["installments"])  # type: ignore[arg-type]
        obligations.append(
            CashFlowObligation(
                due_date=payment_due_date,
                credit_card_id=credit_card_id,
                statement_cycle_end_date=bucket["statement_cycle_end_date"],  # type: ignore[arg-type]
                cash_flow_year=payment_due_date.year,
                cash_flow_month=payment_due_date.month,
                cash_flow_period=f"{payment_due_date.year:04d}-{payment_due_date.month:02d}",
                currency=bucket["currency"],  # type: ignore[arg-type]
                total_amount=bucket["total_amount"],  # type: ignore[arg-type]
                installments=installments_for_group,
            )
        )

    return obligations


def _sort_key(item: tuple[tuple[str, date], dict[str, object]]) -> tuple[date, str]:
    (credit_card_id, payment_due_date), _bucket = item
    return payment_due_date, credit_card_id

