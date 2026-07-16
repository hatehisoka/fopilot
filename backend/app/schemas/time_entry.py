"""TimeEntry schemas."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel, Field

from app.schemas.common import ORMModel


class TimeEntryBase(BaseModel):
    project_id: int
    work_date: date
    hours: Decimal = Field(gt=0, max_digits=6, decimal_places=2)
    description: str | None = Field(default=None, max_length=500)
    billable: bool = True


class TimeEntryCreate(TimeEntryBase):
    pass


class TimeEntryUpdate(BaseModel):
    work_date: date | None = None
    hours: Decimal | None = Field(default=None, gt=0, max_digits=6, decimal_places=2)
    description: str | None = Field(default=None, max_length=500)
    billable: bool | None = None


class TimeEntryRead(TimeEntryBase, ORMModel):
    id: int
