"""Calculation rules for BNPL Cash Flow Tracker."""

from bnpl_cashflow.rules.installments import generate_installments
from bnpl_cashflow.rules.statement_cycles import map_statement_cycle

__all__ = ["generate_installments", "map_statement_cycle"]
