"""Project — a billable engagement for a client."""

from __future__ import annotations

from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Enum as SAEnum
from sqlalchemy import ForeignKey, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.models.enums import ProjectStatus

if TYPE_CHECKING:
    from app.models.client import Client
    from app.models.time_entry import TimeEntry


class Project(Base):
    __tablename__ = "project"

    id: Mapped[int] = mapped_column(primary_key=True)
    client_id: Mapped[int] = mapped_column(ForeignKey("client.id", ondelete="CASCADE"))
    name: Mapped[str] = mapped_column(String(200))
    hourly_rate: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[ProjectStatus] = mapped_column(
        SAEnum(ProjectStatus, name="project_status"), default=ProjectStatus.active
    )

    client: Mapped[Client] = relationship(back_populates="projects")
    time_entries: Mapped[list[TimeEntry]] = relationship(
        back_populates="project", cascade="all, delete-orphan"
    )
