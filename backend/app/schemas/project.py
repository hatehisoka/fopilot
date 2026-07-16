"""Project schemas."""

from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import ProjectStatus
from app.schemas.common import Currency, ORMModel


class ProjectBase(BaseModel):
    client_id: int
    name: str = Field(min_length=1, max_length=200)
    hourly_rate: Decimal = Field(ge=0, max_digits=12, decimal_places=2)
    currency: Currency
    status: ProjectStatus = ProjectStatus.active


class ProjectCreate(ProjectBase):
    pass


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    hourly_rate: Decimal | None = Field(default=None, ge=0, max_digits=12, decimal_places=2)
    currency: Currency | None = None
    status: ProjectStatus | None = None


class ProjectRead(ProjectBase, ORMModel):
    id: int
