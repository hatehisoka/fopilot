"""Invoice repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Invoice
from app.repositories.base import BaseRepository


class InvoiceRepository(BaseRepository[Invoice]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Invoice)

    def get_by_number(self, number: str) -> Invoice | None:
        return self.db.scalar(select(Invoice).where(Invoice.number == number))
