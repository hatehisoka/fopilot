"""ExchangeRate — cached NBU rate for a currency on a date (see ADR-006)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import Date, Numeric, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.db import Base


class ExchangeRate(Base):
    __tablename__ = "exchange_rate"

    id: Mapped[int] = mapped_column(primary_key=True)
    currency: Mapped[str] = mapped_column(String(3))
    rate_date: Mapped[date] = mapped_column(Date)
    rate: Mapped[Decimal] = mapped_column(Numeric(14, 6))
    # Provenance: NULL means the rate was published by the NBU for rate_date;
    # a value means it was taken via weekend/holiday fallback from that (earlier)
    # banking day (see ADR-006).
    source_date: Mapped[date | None] = mapped_column(Date)

    __table_args__ = (
        UniqueConstraint("currency", "rate_date", name="uq_exchange_rate_currency_date"),
    )
