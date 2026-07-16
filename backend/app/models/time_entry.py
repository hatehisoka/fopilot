"""TimeEntry — a logged block of worked hours on a project."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Date, ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base

if TYPE_CHECKING:
    from app.models.invoice import InvoiceItem
    from app.models.project import Project


class TimeEntry(Base):
    __tablename__ = "time_entry"

    id: Mapped[int] = mapped_column(primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("project.id", ondelete="CASCADE"))
    work_date: Mapped[date] = mapped_column(Date)
    hours: Mapped[Decimal] = mapped_column(Numeric(6, 2))
    description: Mapped[str | None] = mapped_column(String(500))
    billable: Mapped[bool] = mapped_column(Boolean, default=True)

    project: Mapped[Project] = relationship(back_populates="time_entries")
    # One time entry is billed into at most one invoice item (see ADR-004).
    invoice_item: Mapped[InvoiceItem | None] = relationship(back_populates="time_entry")
