"""Financial analytics.

Design notes that matter for the numbers (documented as ADRs 014-017):
- Revenue is cash-method: sums of Payment.amount_uah where is_revenue, labelled
  "Надходження". The EP limit is scoped to a calendar year and uses run-rate
  with an insufficient-data guard. Utilization uses a real capacity denominator
  (working days x work_hours_per_day). Everything is UAH; payments without
  amount_uah are surfaced as unconverted_count, never silently dropped into 0.
"""

import math
from datetime import date, timedelta
from decimal import Decimal

import pandas as pd
from sqlalchemy.orm import Session

from app.config import settings
from app.repositories import AnalyticsRepository
from app.schemas import (
    ClientShare,
    ConcentrationReport,
    EpForecast,
    PeriodAmount,
    ProjectUtilization,
    ReceiptsReport,
    UtilizationReport,
)

_CENTS = Decimal("0.01")


def _year_bounds(year: int) -> tuple[date, date]:
    return date(year, 1, 1), date(year, 12, 31)


def _working_days(date_from: date, date_to: date) -> int:
    """Count Mon-Fri days inclusive. Holidays ignored (ADR-016)."""
    if date_to < date_from:
        return 0
    days = (date_to - date_from).days + 1
    return sum(1 for i in range(days) if (date_from + timedelta(days=i)).weekday() < 5)


def _split_converted(payments: list) -> tuple[list, int]:
    converted = [p for p in payments if p.amount_uah is not None]
    unconverted = sum(1 for p in payments if p.amount_uah is None)
    return converted, unconverted


class AnalyticsService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = AnalyticsRepository(db)

    def receipts_by_period(
        self, granularity: str = "month", year: int | None = None
    ) -> ReceiptsReport:
        year = year or date.today().year
        start, end = _year_bounds(year)
        converted, unconverted = _split_converted(self.repo.revenue_payments(start, end))

        periods: list[PeriodAmount] = []
        total = Decimal(0)
        if converted:
            frame = pd.DataFrame(
                {
                    "date": [p.paid_date for p in converted],
                    "amount": [p.amount_uah for p in converted],
                }
            )
            frame["date"] = pd.to_datetime(frame["date"])
            if granularity == "quarter":
                keys = frame["date"].dt.quarter.map(lambda q: f"{year}-Q{q}")
            else:
                keys = frame["date"].dt.month.map(lambda m: f"{year}-{m:02d}")
            grouped = frame["amount"].groupby(keys).apply(lambda s: sum(s, Decimal(0)))
            for label, amount in grouped.sort_index().items():
                periods.append(PeriodAmount(period=label, amount_uah=amount.quantize(_CENTS)))
                total += amount

        return ReceiptsReport(
            granularity="quarter" if granularity == "quarter" else "month",
            year=year,
            periods=periods,
            total_uah=total.quantize(_CENTS),
            unconverted_count=unconverted,
        )

    def utilization(
        self, date_from: date, date_to: date, work_hours_per_day: int | None = None
    ) -> UtilizationReport:
        hours_per_day = work_hours_per_day or settings.work_hours_per_day
        working = _working_days(date_from, date_to)
        capacity = Decimal(working * hours_per_day)

        rows = self.repo.billable_hours_by_project(date_from, date_to)
        projects: list[ProjectUtilization] = []
        total_billable = Decimal(0)
        for pid, name, hours in rows:
            total_billable += hours
            util = float(hours / capacity) if capacity > 0 else None
            projects.append(
                ProjectUtilization(
                    project_id=pid, project_name=name, billable_hours=hours, utilization=util
                )
            )

        overall = float(total_billable / capacity) if capacity > 0 else None
        return UtilizationReport(
            date_from=date_from,
            date_to=date_to,
            working_days=working,
            work_hours_per_day=hours_per_day,
            capacity_hours=capacity,
            total_billable_hours=total_billable,
            overall_utilization=overall,
            projects=projects,
        )

    def concentration(self, year: int | None = None) -> ConcentrationReport:
        year = year or date.today().year
        start, end = _year_bounds(year)

        converted, unconverted = _split_converted(self.repo.revenue_payments(start, end))
        total_converted = sum((p.amount_uah for p in converted), Decimal(0))

        rows = self.repo.attributed_revenue(start, end)
        clients: list[ClientShare] = []
        top_share: float | None = None
        attributed_total = Decimal(0)
        if rows:
            frame = pd.DataFrame(rows, columns=["client_id", "client_name", "amount"])
            grouped = (
                frame.groupby(["client_id", "client_name"])["amount"]
                .apply(lambda s: sum(s, Decimal(0)))
                .sort_values(ascending=False)
            )
            attributed_total = sum(grouped.tolist(), Decimal(0))
            for (cid, name), amount in grouped.items():
                share = float(amount / attributed_total) if attributed_total > 0 else 0.0
                clients.append(
                    ClientShare(
                        client_id=cid,
                        client_name=name,
                        amount_uah=amount.quantize(_CENTS),
                        share=share,
                    )
                )
            top_share = clients[0].share if clients else None

        return ConcentrationReport(
            year=year,
            total_attributed_uah=attributed_total.quantize(_CENTS),
            top_client_share=top_share,
            clients=clients,
            unattributed_uah=(total_converted - attributed_total).quantize(_CENTS),
            unconverted_count=unconverted,
        )

    def ep_forecast(
        self, year: int | None = None, as_of: date | None = None, limit: int | None = None
    ) -> EpForecast:
        today = as_of or date.today()
        year = year or today.year
        start, end = _year_bounds(year)
        effective = min(max(today, start), end)
        limit_value = Decimal(limit if limit is not None else settings.ep_annual_limit)

        converted, unconverted = _split_converted(self.repo.revenue_payments(start, effective))
        received = sum((p.amount_uah for p in converted), Decimal(0))

        days_elapsed = (effective - start).days + 1
        days_in_year = (end - start).days + 1
        share = float(received / limit_value) if limit_value > 0 else 0.0

        run_rate: Decimal | None = None
        projected: Decimal | None = None
        exceed_date: date | None = None
        insufficient = days_elapsed < settings.ep_forecast_min_days

        if not insufficient:
            run_rate = (received / days_elapsed).quantize(_CENTS)
            projected = (run_rate * days_in_year).quantize(_CENTS)
            if received < limit_value and run_rate > 0:
                days_to_exceed = math.ceil(float((limit_value - received) / run_rate))
                exceed_date = effective + timedelta(days=days_to_exceed)

        return EpForecast(
            year=year,
            limit=limit_value,
            received_uah=received.quantize(_CENTS),
            as_of=effective,
            days_elapsed=days_elapsed,
            days_in_year=days_in_year,
            share_of_limit=share,
            run_rate_per_day=run_rate,
            projected_annual=projected,
            projected_exceed_date=exceed_date,
            insufficient_data=insufficient,
            unconverted_count=unconverted,
        )
