"""TimeEntry repository."""

from datetime import date

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models import InvoiceItem, Project, TimeEntry
from app.repositories.base import BaseRepository


class TimeEntryRepository(BaseRepository[TimeEntry]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TimeEntry)

    def list_billable_unbilled(
        self,
        client_id: int,
        project_ids: list[int] | None = None,
        date_from: date | None = None,
        date_to: date | None = None,
    ) -> list[TimeEntry]:
        """Billable time entries of a client not yet linked to any invoice item.

        "Unbilled" = no matching invoice_item (LEFT JOIN … IS NULL). The project
        is eager-loaded so callers can read its rate/currency without N+1.
        """
        stmt = (
            select(TimeEntry)
            .join(Project, TimeEntry.project_id == Project.id)
            .outerjoin(InvoiceItem, InvoiceItem.time_entry_id == TimeEntry.id)
            .options(joinedload(TimeEntry.project))
            .where(Project.client_id == client_id)
            .where(TimeEntry.billable.is_(True))
            .where(InvoiceItem.id.is_(None))
        )
        if project_ids:
            stmt = stmt.where(TimeEntry.project_id.in_(project_ids))
        if date_from is not None:
            stmt = stmt.where(TimeEntry.work_date >= date_from)
        if date_to is not None:
            stmt = stmt.where(TimeEntry.work_date <= date_to)
        stmt = stmt.order_by(TimeEntry.work_date, TimeEntry.id)
        return list(self.db.scalars(stmt).all())
