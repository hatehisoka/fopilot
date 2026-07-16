"""Invoice and InvoiceItem schemas.

`due_date` is optional on create — if omitted, the service derives it from the
client's payment_terms_days (see ADR-005). `amount` on read is the computed
column property (see ADR-003).
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import InvoiceStatus
from app.schemas.common import Currency, ORMModel


class InvoiceItemBase(BaseModel):
    time_entry_id: int | None = None
    description: str = Field(min_length=1, max_length=500)
    quantity: Decimal = Field(gt=0, max_digits=10, decimal_places=2)
    unit_price: Decimal = Field(ge=0, max_digits=12, decimal_places=2)


class InvoiceItemCreate(InvoiceItemBase):
    pass


class InvoiceItemRead(InvoiceItemBase, ORMModel):
    id: int


class InvoiceBase(BaseModel):
    client_id: int
    number: str = Field(min_length=1, max_length=50)
    issue_date: date
    due_date: date | None = None
    currency: Currency
    status: InvoiceStatus = InvoiceStatus.draft


class InvoiceCreate(InvoiceBase):
    items: list[InvoiceItemCreate] = Field(default_factory=list)


class InvoiceUpdate(BaseModel):
    number: str | None = Field(default=None, min_length=1, max_length=50)
    issue_date: date | None = None
    due_date: date | None = None
    currency: Currency | None = None
    status: InvoiceStatus | None = None


class InvoiceRead(ORMModel):
    id: int
    client_id: int
    number: str
    issue_date: date
    due_date: date
    currency: str
    status: InvoiceStatus
    amount: Decimal
    items: list[InvoiceItemRead]
