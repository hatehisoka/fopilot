"""Payment — a received inflow, optionally matched to an invoice (see ADR-001)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import MatchStatus

if TYPE_CHECKING:
    from app.models.bank_transaction import BankTransaction
    from app.models.invoice import Invoice


class Payment(Base):
    __tablename__ = "payment"

    id: Mapped[int] = mapped_column(primary_key=True)
    # Nullable until matched to an invoice.
    invoice_id: Mapped[int | None] = mapped_column(ForeignKey("invoice.id", ondelete="SET NULL"))
    # Nullable for manually entered payments (no bank statement row).
    bank_transaction_id: Mapped[int | None] = mapped_column(
        ForeignKey("bank_transaction.id", ondelete="SET NULL")
    )
    paid_date: Mapped[date] = mapped_column(Date)
    amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    currency: Mapped[str] = mapped_column(String(3))
    # Amount converted to UAH at the NBU rate for paid_date (see ADR-006, ADR-007).
    amount_uah: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    source: Mapped[str | None] = mapped_column(String(200))
    match_status: Mapped[MatchStatus] = mapped_column(
        SAEnum(MatchStatus, name="match_status"), default=MatchStatus.unmatched
    )
    # Whether this inflow counts as ФОП revenue for the single-tax limit. Own-card
    # top-ups, refunds and bank interest are inflows but not revenue (see ADR-012).
    # Orthogonal to match_status: a payment can be revenue without an invoice.
    is_revenue: Mapped[bool] = mapped_column(Boolean, default=True, server_default=text("true"))

    invoice: Mapped[Invoice | None] = relationship(back_populates="payments")
    bank_transaction: Mapped[BankTransaction | None] = relationship(back_populates="payment")

    __table_args__ = (
        # One imported bank row yields at most one payment (ADR-001). Partial so
        # manually entered payments (NULL bank_transaction_id) are unconstrained.
        # This is what makes re-running matching idempotent (ADR-013).
        Index(
            "uq_payment_bank_transaction",
            "bank_transaction_id",
            unique=True,
            postgresql_where=text("bank_transaction_id IS NOT NULL"),
        ),
    )
