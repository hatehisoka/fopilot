"""Data-access layer: repositories wrap SQLAlchemy queries per entity."""

from app.repositories.client import ClientRepository
from app.repositories.invoice import InvoiceRepository
from app.repositories.project import ProjectRepository
from app.repositories.time_entry import TimeEntryRepository

__all__ = [
    "ClientRepository",
    "InvoiceRepository",
    "ProjectRepository",
    "TimeEntryRepository",
]
