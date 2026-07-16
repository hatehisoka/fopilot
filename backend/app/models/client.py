"""Client — a customer of the sole proprietor."""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.invoice import Invoice
    from app.models.project import Project


class Client(Base):
    __tablename__ = "client"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200))
    country: Mapped[str | None] = mapped_column(String(100))
    default_currency: Mapped[str] = mapped_column(String(3))
    # Default payment term used to derive an invoice's due_date (see ADR-005).
    payment_terms_days: Mapped[int] = mapped_column(default=14)
    contacts: Mapped[str | None] = mapped_column(String(500))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    projects: Mapped[list[Project]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
    invoices: Mapped[list[Invoice]] = relationship(
        back_populates="client", cascade="all, delete-orphan"
    )
