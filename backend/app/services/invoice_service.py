"""Invoice business logic.

Beyond plain CRUD this service owns: due_date derivation from the client's
payment terms (ADR-005), building invoices from billable hours (ADR-011), and
translating the DB-level double-billing guard (ADR-004) into a conflict error.
"""

from datetime import date, timedelta

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import Client, Invoice, InvoiceItem
from app.repositories import InvoiceRepository, TimeEntryRepository
from app.schemas import InvoiceBuildRequest, InvoiceCreate, InvoiceUpdate
from app.services.exceptions import ConflictError, NotFoundError


class InvoiceService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = InvoiceRepository(db)
        self.time_entries = TimeEntryRepository(db)

    def get(self, invoice_id: int) -> Invoice:
        invoice = self.repo.get(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Інвойс з id={invoice_id} не знайдено")
        return invoice

    def list(self, offset: int = 0, limit: int = 100) -> list[Invoice]:
        return self.repo.list(offset=offset, limit=limit)

    def create(self, data: InvoiceCreate) -> Invoice:
        client = self._require_client(data.client_id)
        self._ensure_number_free(data.number)

        invoice = Invoice(
            client_id=data.client_id,
            number=data.number,
            issue_date=data.issue_date,
            due_date=self._derive_due_date(data.issue_date, data.due_date, client),
            currency=data.currency,
            status=data.status,
        )
        for item in data.items:
            invoice.items.append(InvoiceItem(**item.model_dump()))

        self.db.add(invoice)
        self._commit()
        self.db.refresh(invoice)
        return invoice

    def build_from_time_entries(self, req: InvoiceBuildRequest) -> Invoice:
        """Assemble an invoice from a client's billable, unbilled hours (ADR-011).

        One invoice item per time entry (quantity = hours, unit_price = the
        project's rate); currency is derived from the projects, not supplied.
        """
        client = self._require_client(req.client_id)
        self._ensure_number_free(req.number)

        entries = self.time_entries.list_billable_unbilled(
            client_id=req.client_id,
            project_ids=req.project_ids,
            date_from=req.date_from,
            date_to=req.date_to,
        )
        if not entries:
            raise ConflictError("Немає оплачуваних незабілених годин за вибраний період")

        currencies = {entry.project.currency for entry in entries}
        if len(currencies) > 1:
            raise ConflictError(
                "Години належать проєктам з різними валютами — згенеруйте окремі інвойси по валютах"
            )
        currency = currencies.pop()

        invoice = Invoice(
            client_id=req.client_id,
            number=req.number,
            issue_date=req.issue_date,
            due_date=self._derive_due_date(req.issue_date, req.due_date, client),
            currency=currency,
        )
        for entry in entries:
            invoice.items.append(
                InvoiceItem(
                    time_entry_id=entry.id,
                    description=entry.description or entry.project.name,
                    quantity=entry.hours,
                    unit_price=entry.project.hourly_rate,
                )
            )

        self.db.add(invoice)
        self._commit()
        self.db.refresh(invoice)
        return invoice

    def update(self, invoice_id: int, data: InvoiceUpdate) -> Invoice:
        invoice = self.get(invoice_id)
        fields = data.model_dump(exclude_unset=True)
        if "number" in fields and fields["number"] != invoice.number:
            self._ensure_number_free(fields["number"])
        for field, value in fields.items():
            setattr(invoice, field, value)
        self._commit()
        self.db.refresh(invoice)
        return invoice

    def delete(self, invoice_id: int) -> None:
        invoice = self.get(invoice_id)
        self.db.delete(invoice)
        self.db.commit()

    def _require_client(self, client_id: int) -> Client:
        client = self.db.get(Client, client_id)
        if client is None:
            raise NotFoundError(f"Клієнта з id={client_id} не знайдено")
        return client

    def _ensure_number_free(self, number: str) -> None:
        if self.repo.get_by_number(number) is not None:
            raise ConflictError(f"Інвойс з номером {number!r} вже існує")

    @staticmethod
    def _derive_due_date(issue_date: date, due_date: date | None, client: Client) -> date:
        return due_date or issue_date + timedelta(days=client.payment_terms_days)

    def _commit(self) -> None:
        """Commit, mapping the partial-index violation to a conflict error."""
        try:
            self.db.commit()
        except IntegrityError as exc:
            self.db.rollback()
            raise ConflictError(
                "Годину вже включено в іншу позицію інвойса (подвійний білинг)"
            ) from exc
