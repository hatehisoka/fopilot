"""Read-only queries feeding the analytics service."""

from datetime import date
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import Client, Invoice, Payment, Project, TimeEntry


class AnalyticsRepository:
    def __init__(self, db: Session) -> None:
        self.db = db

    def revenue_payments(self, date_from: date, date_to: date) -> list[Payment]:
        """All revenue payments in the range (converted or not)."""
        stmt = select(Payment).where(
            Payment.is_revenue.is_(True),
            Payment.paid_date >= date_from,
            Payment.paid_date <= date_to,
        )
        return list(self.db.scalars(stmt).all())

    def attributed_revenue(self, date_from: date, date_to: date) -> list[tuple[int, str, Decimal]]:
        """Converted revenue linked to a client via its invoice."""
        stmt = (
            select(Client.id, Client.name, Payment.amount_uah)
            .join(Invoice, Invoice.id == Payment.invoice_id)
            .join(Client, Client.id == Invoice.client_id)
            .where(
                Payment.is_revenue.is_(True),
                Payment.amount_uah.is_not(None),
                Payment.paid_date >= date_from,
                Payment.paid_date <= date_to,
            )
        )
        return [(cid, name, amount) for cid, name, amount in self.db.execute(stmt).all()]

    def billable_hours_by_project(
        self, date_from: date, date_to: date
    ) -> list[tuple[int, str, Decimal]]:
        stmt = (
            select(Project.id, Project.name, func.coalesce(func.sum(TimeEntry.hours), 0))
            .join(TimeEntry, TimeEntry.project_id == Project.id)
            .where(
                TimeEntry.billable.is_(True),
                TimeEntry.work_date >= date_from,
                TimeEntry.work_date <= date_to,
            )
            .group_by(Project.id, Project.name)
            .order_by(Project.id)
        )
        return [(pid, name, Decimal(hours)) for pid, name, hours in self.db.execute(stmt).all()]
