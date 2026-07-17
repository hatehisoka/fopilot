"""Analytics response schemas.

All money is UAH via Payment.amount_uah. Every money report exposes
`unconverted_count` — payments whose amount_uah is missing — so a data gap is
visible instead of silently lowering the numbers.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class PeriodAmount(BaseModel):
    period: str  # "2026-03" for month, "2026-Q1" for quarter
    amount_uah: Decimal


class ReceiptsReport(BaseModel):
    """Cash-method receipts by period ("Надходження", not accrual revenue)."""

    granularity: str
    year: int
    periods: list[PeriodAmount]
    total_uah: Decimal
    unconverted_count: int


class ProjectUtilization(BaseModel):
    project_id: int
    project_name: str
    billable_hours: Decimal
    utilization: float | None  # billable hours / capacity; None if capacity is 0


class UtilizationReport(BaseModel):
    date_from: date
    date_to: date
    working_days: int
    work_hours_per_day: int
    capacity_hours: Decimal
    total_billable_hours: Decimal
    overall_utilization: float | None
    projects: list[ProjectUtilization]


class ClientShare(BaseModel):
    client_id: int
    client_name: str
    amount_uah: Decimal
    share: float  # of attributed revenue, 0..1


class ConcentrationReport(BaseModel):
    year: int
    total_attributed_uah: Decimal
    top_client_share: float | None  # risk indicator; None when there is no revenue
    clients: list[ClientShare]
    unattributed_uah: Decimal  # revenue not linked to any invoice/client
    unconverted_count: int


class EpForecast(BaseModel):
    year: int
    limit: Decimal
    received_uah: Decimal
    as_of: date
    days_elapsed: int
    days_in_year: int
    share_of_limit: float
    run_rate_per_day: Decimal | None
    projected_annual: Decimal | None
    projected_exceed_date: date | None
    insufficient_data: bool
    unconverted_count: int
