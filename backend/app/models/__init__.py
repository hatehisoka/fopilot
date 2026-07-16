"""ORM models package.

Importing this module registers every model on ``Base.metadata`` (used by Alembic)
and defines the computed ``Invoice.amount`` column property.
"""

from sqlalchemy import func, select
from sqlalchemy.orm import column_property

from app.models.bank_transaction import BankTransaction
from app.models.client import Client
from app.models.enums import InvoiceStatus, MatchStatus, ProjectStatus
from app.models.exchange_rate import ExchangeRate
from app.models.invoice import Invoice, InvoiceItem
from app.models.payment import Payment
from app.models.project import Project
from app.models.time_entry import TimeEntry

# Invoice total as a correlated-subquery column property, not a stored column
# (ADR-003). Defined here, after both classes are mapped, to avoid a circular
# reference between Invoice and InvoiceItem.
Invoice.amount = column_property(
    select(func.coalesce(func.sum(InvoiceItem.quantity * InvoiceItem.unit_price), 0))
    .where(InvoiceItem.invoice_id == Invoice.id)
    .scalar_subquery(),
)

__all__ = [
    "BankTransaction",
    "Client",
    "ExchangeRate",
    "Invoice",
    "InvoiceItem",
    "InvoiceStatus",
    "MatchStatus",
    "Payment",
    "Project",
    "ProjectStatus",
    "TimeEntry",
]
