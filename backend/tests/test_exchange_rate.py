"""Tests for NBU rate resolution, caching and the weekend fallback (ADR-006).

A fake NBU client is injected so tests never touch the network; the DB fixture
provides the real rate cache.
"""

from datetime import date
from decimal import Decimal

import pytest
from sqlalchemy.orm import Session

from app.services.exceptions import RateUnavailableError
from app.services.nbu import ExchangeRateService


class FakeNbuClient:
    """In-memory stand-in for the NBU API that records every call."""

    def __init__(self, rates: dict[date, Decimal]) -> None:
        self.rates = rates
        self.calls: list[date] = []

    def fetch_rate(self, currency: str, on_date: date) -> Decimal | None:
        self.calls.append(on_date)
        return self.rates.get(on_date)


def test_uah_needs_no_lookup(db: Session) -> None:
    fake = FakeNbuClient({})
    service = ExchangeRateService(db, fetcher=fake)
    assert service.get_rate("UAH", date(2026, 2, 7)) == Decimal(1)
    assert fake.calls == []  # base currency never hits the API


def test_rate_is_cached_after_first_fetch(db: Session) -> None:
    fake = FakeNbuClient({date(2026, 2, 6): Decimal("41.50")})
    service = ExchangeRateService(db, fetcher=fake)

    assert service.get_rate("USD", date(2026, 2, 6)) == Decimal("41.50")
    assert service.get_rate("USD", date(2026, 2, 6)) == Decimal("41.50")
    # Same date must be fetched from the API only once.
    assert fake.calls == [date(2026, 2, 6)]


def test_saturday_payment_falls_back_to_last_banking_day(db: Session) -> None:
    saturday = date(2026, 2, 7)
    friday = date(2026, 2, 6)
    assert saturday.weekday() == 5  # self-documenting: it really is Saturday
    fake = FakeNbuClient({friday: Decimal("41.50")})  # no rate on the weekend
    service = ExchangeRateService(db, fetcher=fake)

    rate = service.get_rate("USD", saturday)
    assert rate == Decimal("41.50")  # Friday's rate
    # Walked Saturday (empty) then Friday (hit).
    assert fake.calls == [saturday, friday]

    # Resolved rate is cached under the requested Saturday, so no more API calls.
    assert service.get_rate("USD", saturday) == Decimal("41.50")
    assert fake.calls == [saturday, friday]


def test_rate_found_at_lookback_boundary(db: Session) -> None:
    requested = date(2026, 2, 9)
    seven_days_back = date(2026, 2, 2)
    fake = FakeNbuClient({seven_days_back: Decimal("40.00")})
    service = ExchangeRateService(db, fetcher=fake, max_lookback_days=7)
    assert service.get_rate("USD", requested) == Decimal("40.00")


def test_raises_when_no_rate_within_window(db: Session) -> None:
    fake = FakeNbuClient({})  # NBU has nothing at all
    service = ExchangeRateService(db, fetcher=fake, max_lookback_days=7)
    with pytest.raises(RateUnavailableError):
        service.get_rate("USD", date(2026, 2, 9))
    # Probed exactly the window: requested day plus 7 days back.
    assert len(fake.calls) == 8


def test_convert_to_uah_quantizes_to_cents(db: Session) -> None:
    fake = FakeNbuClient({date(2026, 2, 6): Decimal("41.4567")})
    service = ExchangeRateService(db, fetcher=fake)
    result = service.convert_to_uah(Decimal("100"), "USD", date(2026, 2, 6))
    assert result == Decimal("4145.67")
