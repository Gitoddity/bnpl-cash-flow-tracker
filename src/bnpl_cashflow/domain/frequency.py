from __future__ import annotations

from enum import Enum


class InstallmentFrequency(str, Enum):
    BIWEEKLY = "BIWEEKLY"
    WEEKLY = "WEEKLY"
    MONTHLY = "MONTHLY"

