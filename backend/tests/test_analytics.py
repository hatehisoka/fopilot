"""Tests for analytics, with the edge cases that otherwise print wrong numbers."""

from datetime import date
from decimal import Decimal

from sqlalchemy.orm import Session

from app.models import Client, Invoice, Payment, Project, TimeEntry
from app.services import AnalyticsService


def _client(db: Session, name: str = "Client") -> Client:
    obj = Client(name=name, default_currency="UAH")
    db.add(obj)
    db.flush()
    return obj


def _invoice(db: Session, client_id: int, number: str) -> Invoice:
    inv = Invoice(
        client_id=client_id,
        number=number,
        issue_date=date(2026, 1, 1),
        due_date=date(2026, 1, 15),
        currency="UAH",
    )
    db.add(inv)
    db.flush()
    return inv


def _payment(
    db: Session,
    amount_uah: str | None,
    paid_date: date,
    is_revenue: bool = True,
    invoice_id: int | None = None,
) -> Payment:
    pay = Payment(
        invoice_id=invoice_id,
        paid_date=paid_date,
        amount=Decimal("1"),
        currency="UAH",
        amount_uah=Decimal(amount_uah) if amount_uah is not None else None,
        is_revenue=is_revenue,
    )
    db.add(pay)
    db.flush()
    return pay


def _project(db: Session, client_id: int) -> Project:
    proj = Project(client_id=client_id, name="P", hourly_rate=Decimal("50"), currency="UAH")
    db.add(proj)
    db.flush()
    return proj


def _hours(db: Session, project_id: int, hours: str, day: date, billable: bool = True) -> None:
    db.add(TimeEntry(project_id=project_id, work_date=day, hours=Decimal(hours), billable=billable))
    db.flush()


# --- receipts by period ---------------------------------------------------


def test_receipts_grouped_by_month(db: Session) -> None:
    _payment(db, "100", date(2026, 1, 10))
    _payment(db, "200", date(2026, 2, 5))
    _payment(db, "50", date(2026, 2, 20))
    _payment(db, "999", date(2025, 12, 31))  # previous year, excluded

    report = AnalyticsService(db).receipts_by_period("month", year=2026)
    by_period = {p.period: p.amount_uah for p in report.periods}
    assert by_period == {"2026-01": Decimal("100.00"), "2026-02": Decimal("250.00")}
    assert report.total_uah == Decimal("350.00")
    assert report.unconverted_count == 0


def test_receipts_quarterly_and_flags(db: Session) -> None:
    _payment(db, "100", date(2026, 1, 10))
    _payment(db, "300", date(2026, 3, 20))  # same quarter
    _payment(db, None, date(2026, 2, 2))  # unconverted -> counter, not sum
    _payment(db, "500", date(2026, 2, 2), is_revenue=False)  # not revenue -> excluded

    report = AnalyticsService(db).receipts_by_period("quarter", year=2026)
    by_period = {p.period: p.amount_uah for p in report.periods}
    assert by_period == {"2026-Q1": Decimal("400.00")}
    assert report.unconverted_count == 1


def test_receipts_empty_db(db: Session) -> None:
    report = AnalyticsService(db).receipts_by_period("month", year=2026)
    assert report.periods == []
    assert report.total_uah == Decimal("0.00")
    assert report.unconverted_count == 0


# --- utilization ----------------------------------------------------------


def test_utilization_normal(db: Session) -> None:
    c = _client(db)
    p = _project(db, c.id)
    # Mon 2026-02-02 .. Fri 2026-02-06 = 5 working days, capacity = 5*8 = 40.
    _hours(db, p.id, "20", date(2026, 2, 3))
    _hours(db, p.id, "4", date(2026, 2, 4), billable=False)  # excluded

    report = AnalyticsService(db).utilization(date(2026, 2, 2), date(2026, 2, 6))
    assert report.working_days == 5
    assert report.capacity_hours == Decimal("40")
    assert report.total_billable_hours == Decimal("20")
    assert report.overall_utilization == 0.5
    assert report.projects[0].utilization == 0.5


def test_utilization_zero_hours(db: Session) -> None:
    report = AnalyticsService(db).utilization(date(2026, 2, 2), date(2026, 2, 6))
    assert report.total_billable_hours == Decimal("0")
    assert report.overall_utilization == 0.0  # capacity > 0, no division error
    assert report.projects == []


def test_utilization_zero_capacity_returns_none(db: Session) -> None:
    # Sat + Sun: no working days -> capacity 0 -> utilization None, not a crash.
    report = AnalyticsService(db).utilization(date(2026, 2, 7), date(2026, 2, 8))
    assert report.working_days == 0
    assert report.capacity_hours == Decimal("0")
    assert report.overall_utilization is None


# --- concentration --------------------------------------------------------


def test_concentration_single_client_is_100_percent(db: Session) -> None:
    c = _client(db, "Solo")
    inv = _invoice(db, c.id, "INV-1")
    _payment(db, "1000", date(2026, 3, 1), invoice_id=inv.id)

    report = AnalyticsService(db).concentration(year=2026)
    assert report.top_client_share == 1.0
    assert len(report.clients) == 1
    assert report.clients[0].share == 1.0


def test_concentration_two_clients_shares(db: Session) -> None:
    a = _client(db, "A")
    b = _client(db, "B")
    inv_a = _invoice(db, a.id, "INV-A")
    inv_b = _invoice(db, b.id, "INV-B")
    _payment(db, "300", date(2026, 3, 1), invoice_id=inv_a.id)
    _payment(db, "100", date(2026, 3, 2), invoice_id=inv_b.id)

    report = AnalyticsService(db).concentration(year=2026)
    assert report.total_attributed_uah == Decimal("400.00")
    assert report.clients[0].share == 0.75  # sorted desc, top client first
    assert report.top_client_share == 0.75


def test_concentration_reports_unattributed_and_unconverted(db: Session) -> None:
    c = _client(db, "A")
    inv = _invoice(db, c.id, "INV-A")
    _payment(db, "300", date(2026, 3, 1), invoice_id=inv.id)
    _payment(db, "200", date(2026, 3, 2))  # revenue but no invoice -> unattributed
    _payment(db, None, date(2026, 3, 3))  # unconverted

    report = AnalyticsService(db).concentration(year=2026)
    assert report.total_attributed_uah == Decimal("300.00")
    assert report.unattributed_uah == Decimal("200.00")
    assert report.unconverted_count == 1


def test_concentration_empty_db(db: Session) -> None:
    report = AnalyticsService(db).concentration(year=2026)
    assert report.total_attributed_uah == Decimal("0.00")
    assert report.top_client_share is None
    assert report.clients == []


# --- EP forecast ----------------------------------------------------------


def test_ep_forecast_run_rate(db: Session) -> None:
    # Day 100 of 2026, received 10 000 -> run_rate 100/day.
    _payment(db, "10000", date(2026, 2, 1))
    report = AnalyticsService(db).ep_forecast(year=2026, as_of=date(2026, 4, 10), limit=100_000)
    assert report.insufficient_data is False
    assert report.days_elapsed == 100
    assert report.run_rate_per_day == Decimal("100.00")
    assert report.projected_annual == Decimal("36500.00")
    assert report.projected_exceed_date is not None
    assert report.projected_exceed_date > report.as_of


def test_ep_forecast_insufficient_data(db: Session) -> None:
    _payment(db, "5000", date(2026, 1, 5))
    report = AnalyticsService(db).ep_forecast(year=2026, as_of=date(2026, 1, 10))
    assert report.insufficient_data is True
    assert report.run_rate_per_day is None
    assert report.projected_annual is None
    assert report.projected_exceed_date is None


def test_ep_forecast_already_exceeded(db: Session) -> None:
    _payment(db, "5000", date(2026, 1, 15))
    report = AnalyticsService(db).ep_forecast(year=2026, as_of=date(2026, 3, 1), limit=1000)
    assert report.share_of_limit == 5.0
    assert report.projected_exceed_date is None  # already over the limit


def test_ep_forecast_counts_unconverted(db: Session) -> None:
    _payment(db, "1000", date(2026, 2, 1))
    _payment(db, None, date(2026, 2, 2))  # revenue but not converted
    report = AnalyticsService(db).ep_forecast(year=2026, as_of=date(2026, 4, 1), limit=100_000)
    assert report.received_uah == Decimal("1000.00")  # unconverted excluded
    assert report.unconverted_count == 1


def test_ep_forecast_empty_db(db: Session) -> None:
    report = AnalyticsService(db).ep_forecast(year=2026, as_of=date(2026, 6, 1), limit=100_000)
    assert report.received_uah == Decimal("0.00")
    assert report.share_of_limit == 0.0
    assert report.run_rate_per_day == Decimal("0.00")
    assert report.projected_exceed_date is None  # run_rate 0 -> never projected to exceed
