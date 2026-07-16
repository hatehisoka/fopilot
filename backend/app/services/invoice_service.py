"""Invoice business logic.

Beyond plain CRUD this service owns two rules: due_date derivation from the
client's payment terms (ADR-005) and translating the DB-level double-billing
guard (ADR-004) into a friendly conflict error.
"""

from datetime import timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Client, Invoice, InvoiceItem
from app.repositories import InvoiceRepository
from app.schemas import InvoiceCreate, InvoiceUpdate
from app.services.exceptions import ConflictError, NotFoundError


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InvoiceRepository(db)

    def get(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Інвойс з id={invoice_id} не знайдено")
        return invoice

    def list(self, offset: int = 0, limit: int = 100) -> list[Invoice]:
        return self.repo.list(offset=offset, limit=limit)

    def create(self, data: InvoiceCreate) -> Invoice:
        client = self.db.get(Client, data.client_id)
        if client is None:
            raise NotFoundError(f"Клієнта з id={data.client_id} не знайдено")
        if self.repo.get_by_number(data.number) is not None:
            raise ConflictError(f"Інвойс з номером {data.number!r} вже існує")

        due_date = data.due_date or data.issue_date + timedelta(days=client.payment_terms_days)
        invoice = Invoice(
            client_id=data.client_id,
            number=data.number,
            issue_date=data.issue_date,
            due_date=due_date,
            currency=data.currency,
            status=data.status,
        )
        for item in data.items:
            invoice.items.append(InvoiceItem(**item.model_dump()))

        self.db.add(invoice)
        self._commit()
        self.db.refresh(invoice)
        return invoice

    def update(self, invoice_id: int, data: InvoiceUpdate) -> Invoice:
        invoice = self.get(invoice_id)
        fields = data.model_dump(exclude_unset=True)
        if "number" in fields and fields["number"] != invoice.number:
            if self.repo.get_by_number(fields["number"]) is not None:
                raise ConflictError(f"Інвойс з номером {fields['number']!r} вже існує")
        for field, value in fields.items():
            setattr(invoice, field, value)
        self._commit()
        self.db.refresh(invoice)
        return invoice

    def delete(self, invoice_id: int) -> None:
        invoice = self.get(invoice_id)
        self.db.delete(invoice)
        self.db.commit()

    def _commit(self) -> None:
        """Commit, mapping the partial-index violation to a conflict error."""
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "Годину вже включено в іншу позицію інвойса (подвійний білинг)"
            ) from exc
