"""Payment repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Payment
from app.models.enums import MatchStatus
from app.repositories.base import BaseRepository


class PaymentRepository(BaseRepository[Payment]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Payment)

    def list_filtered(
        self,
        match_status: MatchStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        stmt = select(Payment).order_by(Payment.paid_date.desc(), Payment.id.desc())
        if match_status is not None:
            stmt = stmt.where(Payment.match_status == match_status)
        stmt = stmt.offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())
