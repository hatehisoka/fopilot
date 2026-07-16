"""Match imported inflows to invoices (see ADR-013).

Generates a Payment from each incoming bank transaction, converts it to UAH,
and decides a match. Scope is deliberately narrow: only an exact amount match
confirmed by the invoice number in the description is auto-matched; everything
ambiguous goes to needs_review for a human. Runs are idempotent (one payment
per bank row) and poly-transactional (a rate failure on one payment does not
abort the rest).
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models import BankTransaction, Invoice, Payment
from app.models.enums import MatchStatus
from app.repositories import BankTransactionRepository, InvoiceRepository
from app.schemas import MatchRunError, MatchRunReport
from app.services.exceptions import RateUnavailableError
from app.services.nbu import ExchangeRateService


class MatchingService:
    def __init__(self, db: Session, rates: ExchangeRateService | None = None) -> None:
        self.db = db
        self.bank_txns = BankTransactionRepository(db)
        self.invoices = InvoiceRepository(db)
        self.rates = rates or ExchangeRateService(db)

    def run(self) -> MatchRunReport:
        transactions = self.bank_txns.list_incoming_without_payment()
        invoices = self.invoices.list_all()

        created = auto = review = unmatched = 0
        errors: list[MatchRunError] = []

        for bt in transactions:
            try:
                amount_uah = self.rates.convert_to_uah(bt.amount, bt.currency, bt.tx_date)
            except RateUnavailableError as exc:
                # Skip this one, keep going; it will be retried on the next run.
                errors.append(MatchRunError(bank_transaction_id=bt.id, message=str(exc)))
                continue

            status, invoice_id = self._match(bt, invoices)
            payment = Payment(
                bank_transaction_id=bt.id,
                paid_date=bt.tx_date,
                amount=bt.amount,
                currency=bt.currency,
                amount_uah=amount_uah,
                source=bt.counterparty or bt.description,
                match_status=status,
                invoice_id=invoice_id,
            )
            self.db.add(payment)
            try:
                # Per-payment commit: isolates rate errors and lets the partial
                # unique index reject a duplicate from a concurrent/repeat run.
                self.db.commit()
            except IntegrityError:
                self.db.rollback()
                continue

            created += 1
            if status is MatchStatus.auto:
                auto += 1
            elif status is MatchStatus.needs_review:
                review += 1
            else:
                unmatched += 1

        return MatchRunReport(
            created=created,
            auto_matched=auto,
            needs_review=review,
            unmatched=unmatched,
            errors=errors,
        )

    @staticmethod
    def _match(bt: BankTransaction, invoices: list[Invoice]) -> tuple[MatchStatus, int | None]:
        """Decide a match for one transaction. See ADR-013 for the scope."""
        description = bt.description or ""
        number_matches = [inv for inv in invoices if inv.number and inv.number in description]

        if number_matches:
            if len(number_matches) > 1:
                # Several invoice numbers in one payment (split) — out of scope.
                return MatchStatus.needs_review, None
            invoice = number_matches[0]
            if invoice.currency == bt.currency and invoice.amount == bt.amount:
                return MatchStatus.auto, invoice.id
            # Number matched but amount differs (partial/overpay): suggest, review.
            return MatchStatus.needs_review, invoice.id

        # No number in the description — fall back to an exact amount+currency hit.
        exact = [inv for inv in invoices if inv.currency == bt.currency and inv.amount == bt.amount]
        if len(exact) == 1:
            # Amount matches but is unconfirmed by a number — suggest, review.
            return MatchStatus.needs_review, exact[0].id
        return MatchStatus.unmatched, None
