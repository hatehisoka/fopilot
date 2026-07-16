"""ExchangeRate repository (rate cache)."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import ExchangeRate
from app.repositories.base import BaseRepository


class ExchangeRateRepository(BaseRepository[ExchangeRate]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, ExchangeRate)

    def get_for(self, currency: str, rate_date: date) -> ExchangeRate | None:
        stmt = select(ExchangeRate).where(
            ExchangeRate.currency == currency, ExchangeRate.rate_date == rate_date
        )
        return self.db.scalar(stmt)
