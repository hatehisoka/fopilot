"""BankTransaction repository."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import BankTransaction, Payment
from app.repositories.base import BaseRepository


class BankTransactionRepository(BaseRepository[BankTransaction]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, BankTransaction)

    def existing_hashes(self, hashes: list[str]) -> set[str]:
        """Return which of the given row hashes already exist (batch dedup)."""
        if not hashes:
            return set()
        stmt = select(BankTransaction.row_hash).where(BankTransaction.row_hash.in_(hashes))
        return set(self.db.scalars(stmt).all())

    def list_incoming_without_payment(self) -> list[BankTransaction]:
        """Credit (incoming) rows that have no payment yet — matching candidates."""
        stmt = (
            select(BankTransaction)
            .outerjoin(Payment, Payment.bank_transaction_id == BankTransaction.id)
            .where(BankTransaction.amount > 0)
            .where(Payment.id.is_(None))
            .order_by(BankTransaction.tx_date, BankTransaction.id)
        )
        return list(self.db.scalars(stmt).all())
