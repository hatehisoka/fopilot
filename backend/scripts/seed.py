"""Generate synthetic but plausible demo data for FOPilot.

Design goals (each maps to a review requirement):
1. Dates are relative to today (Jan 1 of the current year .. today), so the EP
   forecast never rots into insufficient_data / empty year.
2. Deterministic: a fixed RNG seed makes two runs identical.
3. Idempotent: refuses to run on a non-empty DB unless --force, which truncates
   first.
4. NBU rates come from an offline JSON snapshot, not the live API.
5. The scenario lights up every dashboard metric (see MODULE docstring below).
6. Writes two sample CSV statements for a live import demo (UTF-8 + cp1251 with
   a broken row and a legit duplicate).

Run:  python scripts/seed.py [--force]
"""

from __future__ import annotations

import argparse
import csv
import io
import json
import random
import sys
from datetime import date, timedelta
from decimal import Decimal
from pathlib import Path

# Make `app` importable regardless of how the script is invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text  # noqa: E402

from app.config import settings  # noqa: E402
from app.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    BankTransaction,  # noqa: F401  (kept for TRUNCATE table list clarity)
    Client,
    ExchangeRate,
    Invoice,
    InvoiceItem,
    Payment,
    Project,
    TimeEntry,
)
from app.models.enums import InvoiceStatus, MatchStatus, ProjectStatus  # noqa: E402
from app.services import AnalyticsService  # noqa: E402

SEED = 42
CENTS = Decimal("0.01")
SNAPSHOT_PATH = Path(__file__).resolve().parent / "nbu_rates_snapshot.json"
SCRIPTS_DIR = Path(__file__).resolve().parent

# Share of the annual EP limit billed per month. Tuned so that by mid-year the
# received revenue sits around ~80% of the limit and the run-rate projects over
# it (shows an exceedance date rather than "all good").
MONTHLY_FRACTION = Decimal("0.145")

_TABLES = [
    "invoice_item",
    "payment",
    "time_entry",
    "invoice",
    "project",
    "bank_transaction",
    "exchange_rate",
    "client",
]

# Plausible clients for KVED 62.01: mix of foreign and Ukrainian, rates 25-45
# USD/hr (UAH clients priced in hryvnia). One dominant client (~50%).
CLIENT_SPECS = [
    {
        "name": "Northwind Software Inc.",
        "country": "USA",
        "currency": "USD",
        "code": "NW",
        "share": Decimal("0.50"),
        "rate": Decimal("45"),
        "terms": 21,
    },
    {
        "name": "Helvetia Digital GmbH",
        "country": "Germany",
        "currency": "EUR",
        "code": "HD",
        "share": Decimal("0.20"),
        "rate": Decimal("40"),
        "terms": 30,
    },
    {
        "name": "BrightApps Ltd.",
        "country": "United Kingdom",
        "currency": "USD",
        "code": "BA",
        "share": Decimal("0.15"),
        "rate": Decimal("35"),
        "terms": 14,
    },
    {
        "name": "ТОВ «Аграріум»",
        "country": "Ukraine",
        "currency": "UAH",
        "code": "AGR",
        "share": Decimal("0.10"),
        "rate": Decimal("1400"),
        "terms": 14,
    },
    {
        "name": "ФОП Коваленко О. П.",
        "country": "Ukraine",
        "currency": "UAH",
        "code": "KOV",
        "share": Decimal("0.05"),
        "rate": Decimal("1100"),
        "terms": 14,
    },
]


def load_rates() -> dict:
    data = json.loads(SNAPSHOT_PATH.read_text(encoding="utf-8"))
    return {cur: data[cur] for cur in ("USD", "EUR")}


def rate_for(rates: dict, currency: str, month: int) -> Decimal:
    if currency == "UAH":
        return Decimal(1)
    return Decimal(rates[currency][str(month)])


def working_days(year: int, month: int, not_after: date) -> list[date]:
    day = date(year, month, 1)
    result = []
    while day.month == month and day <= not_after:
        if day.weekday() < 5:
            result.append(day)
        day += timedelta(days=1)
    return result


def is_empty(session) -> bool:
    return session.query(Client).first() is None


def truncate(session) -> None:
    session.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    session.commit()


def seed_exchange_rates(session, rates: dict, year: int) -> None:
    for currency, by_month in rates.items():
        for month_str, value in by_month.items():
            session.add(
                ExchangeRate(
                    currency=currency,
                    rate_date=date(year, int(month_str), 1),
                    rate=Decimal(value),
                    source_date=None,
                )
            )
    session.flush()


def main(force: bool) -> None:
    rng = random.Random(SEED)
    rates = load_rates()
    today = date.today()
    year = today.year
    months = list(range(1, today.month + 1))
    monthly_target = Decimal(settings.ep_annual_limit) * MONTHLY_FRACTION

    session = SessionLocal()
    try:
        if not is_empty(session):
            if not force:
                print(
                    "База не порожня. Повторний запуск затре дані. "
                    "Використайте --force, щоб очистити й наповнити заново."
                )
                return
            truncate(session)

        seed_exchange_rates(session, rates, year)

        # Clients + one project each.
        clients: list[tuple[dict, Client, Project]] = []
        for spec in CLIENT_SPECS:
            client = Client(
                name=spec["name"],
                country=spec["country"],
                default_currency=spec["currency"],
                payment_terms_days=spec["terms"],
                contacts=f"billing@{spec['code'].lower()}.example",
            )
            session.add(client)
            session.flush()
            project = Project(
                client_id=client.id,
                name=f"Розробка ПЗ — {spec['name']}",
                hourly_rate=spec["rate"],
                currency=spec["currency"],
                status=ProjectStatus.active,
            )
            session.add(project)
            session.flush()
            clients.append((spec, client, project))

        dip_month = today.month - 2 if today.month >= 4 else None
        overdue_month = today.month - 2 if today.month >= 3 else None
        review_month = today.month - 1 if today.month >= 2 else None

        received_uah = Decimal(0)
        unpaid_uah_invoices: list[tuple[str, Decimal]] = []

        for month in months:
            is_current = month == today.month
            issue_day = min(3, today.day) if is_current else 3
            for spec, client, _project in clients:
                rate = rate_for(rates, spec["currency"], month)
                target_ccy = (monthly_target * spec["share"] / rate).quantize(CENTS)
                quantity = (target_ccy / spec["rate"]).quantize(CENTS)
                unit_price = spec["rate"]
                amount_ccy = (quantity * unit_price).quantize(CENTS)

                issue = date(year, month, issue_day)
                due = issue + timedelta(days=spec["terms"])
                invoice = Invoice(
                    client_id=client.id,
                    number=f"{spec['code']}-{year}{month:02d}",
                    issue_date=issue,
                    due_date=due,
                    currency=spec["currency"],
                )
                invoice.items.append(
                    InvoiceItem(
                        description=f"Розробка та підтримка ПЗ, {year}-{month:02d}",
                        quantity=quantity,
                        unit_price=unit_price,
                    )
                )
                session.add(invoice)
                session.flush()

                amount_uah = (amount_ccy * rate).quantize(CENTS)
                # Overdue example on a mid client (not the dominant one, so it does
                # not distort the concentration ~50% signal).
                is_overdue_demo = spec["code"] == "BA" and month == overdue_month
                # A couple of payments left for manual confirmation.
                is_review_demo = spec["code"] in {"HD", "KOV"} and month == review_month

                if is_current or is_overdue_demo:
                    # Leave unpaid: current month is simply recent; the dominant
                    # client's older invoice is the overdue example.
                    invoice.status = InvoiceStatus.overdue if due < today else InvoiceStatus.sent
                    if spec["currency"] == "UAH" and is_current:
                        unpaid_uah_invoices.append((invoice.number, amount_ccy))
                    continue

                paid_date = min(issue + timedelta(days=rng.randint(3, 12)), today)
                status = MatchStatus.needs_review if is_review_demo else MatchStatus.confirmed
                session.add(
                    Payment(
                        invoice_id=invoice.id,
                        paid_date=paid_date,
                        amount=amount_ccy,
                        currency=spec["currency"],
                        amount_uah=amount_uah,
                        source=spec["name"],
                        match_status=status,
                        is_revenue=True,
                    )
                )
                invoice.status = InvoiceStatus.sent if is_review_demo else InvoiceStatus.paid
                received_uah += amount_uah

        # A non-revenue inflow (own-card top-up) — demonstrates ADR-012.
        session.add(
            Payment(
                paid_date=today - timedelta(days=5),
                amount=Decimal("80000"),
                currency="UAH",
                amount_uah=Decimal("80000.00"),
                source="Поповнення власною карткою",
                match_status=MatchStatus.unmatched,
                is_revenue=False,
            )
        )

        seed_time_entries(session, clients, months, year, today, dip_month, rng)
        session.commit()

        write_sample_csv(today, unpaid_uah_invoices)
        write_cp1251_csv(today)

        print_summary(session, received_uah)
    finally:
        session.close()


# Billable hours logged per working day (of 8) -> overall utilization ~0.81.
_BILLABLE_PER_DAY = Decimal("6.5")
_DIP_FACTOR = Decimal("0.22")


def seed_time_entries(session, clients, months, year, today, dip_month, rng) -> None:
    """Log billable hours to drive utilization, with one low-load (dip) month.

    Hours scale with the number of working days available, so a partial current
    month does not blow utilization past 100%.
    """
    for month in months:
        available = working_days(
            year, month, today if month == today.month else date(year, month, 28)
        )
        if not available:
            continue
        factor = _DIP_FACTOR if month == dip_month else Decimal(1)
        for spec, _client, project in clients:
            project_hours = (spec["share"] * _BILLABLE_PER_DAY * len(available) * factor).quantize(
                Decimal("0.1")
            )
            if project_hours <= 0:
                continue
            picks = rng.sample(available, k=min(4, len(available)))
            per_entry = (project_hours / len(picks)).quantize(Decimal("0.1"))
            for i, day in enumerate(picks):
                # Every ~10th entry is non-billable internal work.
                billable = not (i == 0 and rng.random() < 0.1)
                session.add(
                    TimeEntry(
                        project_id=project.id,
                        work_date=day,
                        hours=per_entry,
                        description="Розробка" if billable else "Внутрішні задачі",
                        billable=billable,
                    )
                )
    session.flush()


def write_sample_csv(today: date, unpaid_uah_invoices: list[tuple[str, Decimal]]) -> None:
    """UTF-8 statement (generic profile) with rows that live-match real invoices."""
    rows = [["date", "amount", "currency", "description", "counterparty"]]
    for number, amount in unpaid_uah_invoices:
        rows.append(
            [
                today.isoformat(),
                f"{amount}",
                "UAH",
                f"Оплата рахунку {number}",
                "Український клієнт",
            ]
        )
    rows.append([today.isoformat(), "45000.00", "UAH", "Відшкодування витрат", "Постачальник"])

    buffer = io.StringIO()
    csv.writer(buffer).writerows(rows)
    (SCRIPTS_DIR / "sample_statement.csv").write_text(buffer.getvalue(), encoding="utf-8")


def write_cp1251_csv(today: date) -> None:
    """cp1251 statement (privatbank profile) with a broken row and a legit duplicate."""
    d = today.strftime("%d.%m.%Y")
    lines = [
        "Дата;Сума;Валюта;Призначення платежу;Контрагент",
        f"{d};15 000,00;UAH;Оплата за консультацію;ТОВ Приклад",
        f"{d};15 000,00;UAH;Оплата за консультацію;ТОВ Приклад",  # legit duplicate
        "31.02.2026;9 999,00;UAH;Битий рядок — неможлива дата;Хтось",  # broken row
    ]
    text_content = "\r\n".join(lines) + "\r\n"
    (SCRIPTS_DIR / "sample_statement_win1251.csv").write_bytes(text_content.encode("cp1251"))


def print_summary(session, received_uah: Decimal) -> None:
    analytics = AnalyticsService(session)
    forecast = analytics.ep_forecast()
    concentration = analytics.concentration()
    limit = Decimal(settings.ep_annual_limit)
    print("Готово. Згенеровано демо-дані.")
    print(f"  Отримано (дохід) YTD: {received_uah:,.2f} грн ({received_uah / limit:.0%} ліміту ЄП)")
    print(
        f"  Прогноз перевищення ліміту: {forecast.projected_exceed_date} "
        f"(insufficient_data={forecast.insufficient_data})"
    )
    if concentration.clients:
        top = concentration.clients[0]
        print(f"  Топ-клієнт: {top.client_name} — {top.share:.0%} доходу")
    print(
        "  CSV для демо імпорту: scripts/sample_statement.csv, scripts/sample_statement_win1251.csv"
    )


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Наповнити БД демо-даними FOPilot.")
    parser.add_argument(
        "--force", action="store_true", help="Очистити наявні дані перед наповненням."
    )
    main(parser.parse_args().force)
