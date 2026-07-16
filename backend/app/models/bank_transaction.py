"""BankTransaction — a raw imported bank statement row (see ADR-001)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.payment import Payment


class BankTransaction(Base):
    __tablename__ = "bank_transaction"

    id: Mapped[int] = mapped_column(primary_key=True)
    tx_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    description: Mapped[str | None] = mapped_column(String(500))
    counterparty: Mapped[str | None] = mapped_column(String(200))
    # Deterministic dedup key; includes the row's occurrence index within the
    # file so legitimate identical rows are not collapsed (see ADR-008).
    row_hash: Mapped[str] = mapped_column(String(64), unique=True)
    import_batch_id: Mapped[str] = mapped_column(String(64))

    payment: Mapped[Payment | None] = relationship(back_populates="bank_transaction")
