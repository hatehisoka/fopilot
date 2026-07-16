"""Payment review actions: listing, confirming/rejecting matches, revenue flag."""

from sqlalchemy.orm import Session

from app.models import Invoice, Payment
from app.models.enums import MatchStatus
from app.repositories import PaymentRepository
from app.services.exceptions import ConflictError, NotFoundError


class PaymentService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = PaymentRepository(db)

    def get(self, payment_id: int) -> Payment:
        payment = self.repo.get(payment_id)
        if payment is None:
            raise NotFoundError(f"Платіж з id={payment_id} не знайдено")
        return payment

    def list(
        self,
        match_status: MatchStatus | None = None,
        offset: int = 0,
        limit: int = 100,
    ) -> list[Payment]:
        return self.repo.list_filtered(match_status=match_status, offset=offset, limit=limit)

    def confirm(self, payment_id: int, invoice_id: int | None = None) -> Payment:
        """Confirm a match: use the given invoice, or the payment's suggestion."""
        payment = self.get(payment_id)
        target = invoice_id if invoice_id is not None else payment.invoice_id
        if target is None:
            raise ConflictError("Немає інвойса для підтвердження — вкажіть invoice_id")
        if self.db.get(Invoice, target) is None:
            raise NotFoundError(f"Інвойс з id={target} не знайдено")
        payment.invoice_id = target
        payment.match_status = MatchStatus.confirmed
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def reject(self, payment_id: int) -> Payment:
        """Reject the suggested match, unlinking the invoice."""
        payment = self.get(payment_id)
        payment.invoice_id = None
        payment.match_status = MatchStatus.rejected
        self.db.commit()
        self.db.refresh(payment)
        return payment

    def set_revenue(self, payment_id: int, is_revenue: bool) -> Payment:
        payment = self.get(payment_id)
        payment.is_revenue = is_revenue
        self.db.commit()
        self.db.refresh(payment)
        return payment
