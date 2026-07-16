"""NBU exchange rate integration and UAH conversion (see ADR-006).

The NBU publishes no rate for weekends/holidays, so `ExchangeRateService`
resolves the applicable rate by walking back to the last banking day within a
bounded window, and caches the result in the DB keyed by the *requested* date
so the same date is never fetched from the API twice.
"""

from datetime import date, timedelta
from decimal import Decimal
from typing import Protocol

import httpx
from sqlalchemy.orm import Session

from app.config import settings
from app.models import ExchangeRate
from app.repositories import ExchangeRateRepository
from app.services.exceptions import RateUnavailableError

BASE_CURRENCY = "UAH"
DEFAULT_MAX_LOOKBACK_DAYS = 7


class RateFetcher(Protocol):
    """Anything that can return the NBU rate for a currency on a given day."""

    def fetch_rate(self, currency: str, on_date: date) -> Decimal | None: ...


class NbuClient:
    """Live NBU statdirectory client.

    Returns None when the API has no rate for that date (e.g. a weekend), which
    is the signal for the caller to fall back to an earlier banking day.
    """

    def __init__(self, base_url: str | None = None, http: httpx.Client | None = None) -> None:
        self.base_url = base_url or settings.nbu_rate_url
        self._http = http or httpx.Client(timeout=10.0)

    def fetch_rate(self, currency: str, on_date: date) -> Decimal | None:
        response = self._http.get(
            self.base_url,
            params={"valcode": currency, "date": on_date.strftime("%Y%m%d"), "json": ""},
        )
        response.raise_for_status()
        rows = response.json()
        if not rows:
            return None
        # Convert via str to avoid binary float noise in the Decimal.
        return Decimal(str(rows[0]["rate"]))


class ExchangeRateService:
    def __init__(
        self,
        db: Session,
        fetcher: RateFetcher | None = None,
        max_lookback_days: int = DEFAULT_MAX_LOOKBACK_DAYS,
    ) -> None:
        self.db = db
        self.repo = ExchangeRateRepository(db)
        self.fetcher = fetcher or NbuClient()
        self.max_lookback_days = max_lookback_days

    def get_rate(self, currency: str, on_date: date) -> Decimal:
        """UAH rate for one unit of `currency` applicable on `on_date`.

        UAH resolves to 1. Otherwise: cache hit, else walk back up to
        `max_lookback_days` banking days; raise if nothing is found.
        """
        currency = currency.upper()
        if currency == BASE_CURRENCY:
            return Decimal(1)

        cached = self.repo.get_for(currency, on_date)
        if cached is not None:
            return cached.rate

        for delta in range(self.max_lookback_days + 1):
            candidate = on_date - timedelta(days=delta)
            rate = self.fetcher.fetch_rate(currency, candidate)
            if rate is not None:
                # Cache under the requested date (not the banking day) so a repeat
                # request for the same weekend date is served from cache.
                self.repo.add(ExchangeRate(currency=currency, rate_date=on_date, rate=rate))
                self.db.commit()
                return rate

        raise RateUnavailableError(
            f"Не вдалося знайти курс {currency} на {on_date:%d.%m.%Y} "
            f"за останні {self.max_lookback_days} днів"
        )

    def convert_to_uah(self, amount: Decimal, currency: str, on_date: date) -> Decimal:
        """Convert `amount` in `currency` to UAH using the rate for `on_date`."""
        rate = self.get_rate(currency, on_date)
        return (amount * rate).quantize(Decimal("0.01"))
