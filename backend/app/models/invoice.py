"""Invoice and InvoiceItem.

The invoice total (`Invoice.amount`) is not stored as a column — it is a
``column_property`` defined in ``app/models/__init__.py`` (see ADR-003).
"""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, ForeignKey, Index, Numeric, String, text
from sqlalchemy import Enum as SAEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import InvoiceStatus

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.payment import Payment
    from app.models.time_entry import TimeEntry


class Invoice(Base):
    __tablename__ = "invoice"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"))
    number: Mapped[str] = mapped_column(String(50), unique=True)
    issue_date: Mapped[date] = mapped_column(Date)
    due_date: Mapped[date] = mapped_column(Date)
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[InvoiceStatus] = mapped_column(
        SAEnum(InvoiceStatus, name="invoice_status"), default=InvoiceStatus.draft
    )

    client: Mapped[Client] = relationship(back_populates="invoices")
    items: Mapped[list[InvoiceItem]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan"
    )
    payments: Mapped[list[Payment]] = relationship(back_populates="invoice")


class InvoiceItem(Base):
    __tablename__ = "invoice_item"

    id: Mapped[int] = mapped_column(primary_key=True)
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoice.id", ondelete="CASCADE"))
    # Nullable: an item may originate from a time entry or be added manually.
    time_entry_id: Mapped[int | None] = mapped_column(
        ForeignKey("time_entry.id", ondelete="SET NULL")
    )
    description: Mapped[str] = mapped_column(String(500))
    quantity: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2))

    invoice: Mapped[Invoice] = relationship(back_populates="items")
    time_entry: Mapped[TimeEntry | None] = relationship(back_populates="invoice_item")

    __table_args__ = (
        # Enforce "no double billing" at the DB level: one time entry maps to at
        # most one item. Partial index so multiple manual items (NULL) are allowed.
        Index(
            "uq_invoice_item_time_entry",
            "time_entry_id",
            unique=True,
            postgresql_where=text("time_entry_id IS NOT NULL"),
        ),
    )
