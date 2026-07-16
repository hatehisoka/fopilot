"""Tests for payment-to-invoice matching (ADR-013).

Service-level tests inject a fake rate provider (duck-typed) so no network is
touched and rate failures can be forced. The API end-to-end test uses UAH data,
which short-circuits the rate lookup entirely.
"""

from datetime import date
from decimal import Decimal
from pathlib import Path
from uuid import uuid4

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.models import BankTransaction, Client, Invoice, InvoiceItem, Payment
from app.models.enums import MatchStatus
from app.services import MatchingService
from app.services.exceptions import RateUnavailableError

FIXTURES = Path(__file__).parent / "fixtures"


class FakeRates:
    """Stand-in for ExchangeRateService: 1:1 conversion, forced failures."""

    def __init__(self, unavailable: tuple[str, ...] = ()) -> None:
        self.unavailable = set(unavailable)

    def convert_to_uah(self, amount: Decimal, currency: str, on_date: date) -> Decimal:
        if currency in self.unavailable:
            raise RateUnavailableError(f"немає курсу {currency}")
        return amount


def _client(db: Session) -> Client:
    obj = Client(name="C", default_currency="USD")
    db.add(obj)
    db.flush()
    return obj


def _invoice(
    db: Session, client_id: int, number: str, amount: str, currency: str = "USD"
) -> Invoice:
    inv = Invoice(
        client_id=client_id,
        number=number,
        issue_date=date(2026, 2, 1),
        due_date=date(2026, 2, 15),
        currency=currency,
    )
    inv.items.append(
        InvoiceItem(description="work", quantity=Decimal("1"), unit_price=Decimal(amount))
    )
    db.add(inv)
    db.flush()
    return inv


def _bt(
    db: Session, amount: str, description: str, currency: str = "USD", day: date = date(2026, 2, 10)
) -> BankTransaction:
    bt = BankTransaction(
        tx_date=day,
        amount=Decimal(amount),
        currency=currency,
        description=description,
        counterparty="Payer",
        row_hash=uuid4().hex,
        import_batch_id="test",
    )
    db.add(bt)
    db.flush()
    return bt


def test_exact_amount_and_number_auto_matches(db: Session) -> None:
    c = _client(db)
    inv = _invoice(db, c.id, "INV-100", "500")
    _bt(db, "500", "Payment for INV-100")

    report = MatchingService(db, rates=FakeRates()).run()
    assert (report.created, report.auto_matched, report.needs_review, report.unmatched) == (
        1,
        1,
        0,
        0,
    )

    payment = db.query(Payment).one()
    assert payment.match_status is MatchStatus.auto
    assert payment.invoice_id == inv.id
    assert payment.amount_uah == Decimal("500")


def test_number_match_but_amount_differs_needs_review(db: Session) -> None:
    c = _client(db)
    inv = _invoice(db, c.id, "INV-101", "500")
    _bt(db, "300", "partial pay INV-101")

    report = MatchingService(db, rates=FakeRates()).run()
    assert report.needs_review == 1 and report.auto_matched == 0

    payment = db.query(Payment).one()
    assert payment.match_status is MatchStatus.needs_review
    assert payment.invoice_id == inv.id  # suggested, not confirmed


def test_exact_amount_without_number_needs_review(db: Session) -> None:
    c = _client(db)
    inv = _invoice(db, c.id, "INV-102", "700")
    _bt(db, "700", "no invoice number here")

    report = MatchingService(db, rates=FakeRates()).run()
    assert report.needs_review == 1

    payment = db.query(Payment).one()
    assert payment.invoice_id == inv.id
    assert payment.match_status is MatchStatus.needs_review


def test_no_signal_is_unmatched(db: Session) -> None:
    c = _client(db)
    _invoice(db, c.id, "INV-103", "700")
    _bt(db, "123", "random unrelated transfer")

    report = MatchingService(db, rates=FakeRates()).run()
    assert report.unmatched == 1

    payment = db.query(Payment).one()
    assert payment.match_status is MatchStatus.unmatched
    assert payment.invoice_id is None


def test_multiple_numbers_is_split_needs_review(db: Session) -> None:
    c = _client(db)
    _invoice(db, c.id, "INV-200", "100")
    _invoice(db, c.id, "INV-201", "200")
    _bt(db, "300", "combined INV-200 and INV-201")

    report = MatchingService(db, rates=FakeRates()).run()
    assert report.needs_review == 1

    payment = db.query(Payment).one()
    assert payment.match_status is MatchStatus.needs_review
    assert payment.invoice_id is None  # ambiguous split, no single suggestion


def test_only_incoming_transactions_become_payments(db: Session) -> None:
    c = _client(db)
    _invoice(db, c.id, "INV-300", "500")
    _bt(db, "500", "Payment INV-300")
    _bt(db, "-40", "Bank fee")  # outflow, ignored

    report = MatchingService(db, rates=FakeRates()).run()
    assert report.created == 1  # only the credit

    assert db.query(Payment).count() == 1


def test_matching_is_idempotent(db: Session) -> None:
    c = _client(db)
    _invoice(db, c.id, "INV-400", "500")
    _bt(db, "500", "Payment INV-400")

    service = MatchingService(db, rates=FakeRates())
    first = service.run()
    second = service.run()

    assert first.created == 1
    assert second.created == 0  # nothing new to process

    assert db.query(Payment).count() == 1  # no duplicate payment


def test_rate_failure_does_not_abort_run(db: Session) -> None:
    c = _client(db)
    _invoice(db, c.id, "INV-500", "500", currency="UAH")
    ok = _bt(db, "500", "Payment INV-500", currency="UAH")
    broken = _bt(db, "100", "EUR inflow", currency="EUR")

    report = MatchingService(db, rates=FakeRates(unavailable=("EUR",))).run()

    assert report.created == 1  # the UAH one still processed
    assert report.auto_matched == 1
    assert len(report.errors) == 1
    assert report.errors[0].bank_transaction_id == broken.id
    assert ok.id != broken.id


def test_matching_workflow_via_api(client: TestClient) -> None:
    # Import UAH statement rows (no network needed for UAH conversion).
    imp = client.post(
        "/imports/bank-statement",
        params={"profile": "generic"},
        files={"file": ("s.csv", (FIXTURES / "match_uah.csv").read_bytes(), "text/csv")},
    )
    assert imp.status_code == 200, imp.text

    cl = client.post("/clients", json={"name": "Client A", "default_currency": "UAH"}).json()
    # INV-500 exact + number -> auto; INV-700 exact amount, no number -> needs_review.
    for number, amount in [("INV-500", "500"), ("INV-700", "700")]:
        client.post(
            "/invoices",
            json={
                "client_id": cl["id"],
                "number": number,
                "issue_date": "2026-02-01",
                "currency": "UAH",
                "items": [{"description": "w", "quantity": "1", "unit_price": amount}],
            },
        )

    report = client.post("/payments/match").json()
    # Credits: 500 (auto), 999 (unmatched), 700 (needs_review). Debit -30 ignored.
    assert report["created"] == 3
    assert report["auto_matched"] == 1
    assert report["needs_review"] == 1
    assert report["unmatched"] == 1

    review = client.get("/payments", params={"match_status": "needs_review"}).json()
    assert len(review) == 1
    payment_id = review[0]["id"]

    # Confirm using the suggested invoice (empty body).
    confirmed = client.post(f"/payments/{payment_id}/confirm", json={})
    assert confirmed.status_code == 200
    assert confirmed.json()["match_status"] == "confirmed"

    # Mark the own-card top-up as non-revenue.
    unmatched = client.get("/payments", params={"match_status": "unmatched"}).json()[0]
    patched = client.patch(f"/payments/{unmatched['id']}/revenue", json={"is_revenue": False})
    assert patched.status_code == 200
    assert patched.json()["is_revenue"] is False

    assert len(client.get("/payments", params={"match_status": "confirmed"}).json()) == 1
