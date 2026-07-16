"""Payment and matching schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel

from app.models.enums import MatchStatus
from app.schemas.common import ORMModel


class PaymentRead(ORMModel):
    id: int
    invoice_id: int | None
    bank_transaction_id: int | None
    paid_date: date
    amount: Decimal
    currency: str
    amount_uah: Decimal | None
    source: str | None
    match_status: MatchStatus
    is_revenue: bool


class PaymentConfirm(BaseModel):
    # Which invoice to confirm; if omitted, the payment's suggested invoice is used.
    invoice_id: int | None = None


class PaymentRevenueUpdate(BaseModel):
    is_revenue: bool


class MatchRunError(BaseModel):
    bank_transaction_id: int
    message: str


class MatchRunReport(BaseModel):
    created: int
    auto_matched: int
    needs_review: int
    unmatched: int
    errors: list[MatchRunError]
