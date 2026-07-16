"""Client schemas."""

from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.common import Currency, ORMModel


class ClientBase(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    default_currency: Currency
    payment_terms_days: int = Field(default=14, ge=0, le=365)
    contacts: str | None = Field(default=None, max_length=500)


class ClientCreate(ClientBase):
    pass


class ClientUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    country: str | None = Field(default=None, max_length=100)
    default_currency: Currency | None = None
    payment_terms_days: int | None = Field(default=None, ge=0, le=365)
    contacts: str | None = Field(default=None, max_length=500)


class ClientRead(ClientBase, ORMModel):
    id: int
    created_at: datetime
