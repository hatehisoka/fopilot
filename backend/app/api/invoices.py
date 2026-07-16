"""Invoice CRUD endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    InvoiceBuildRequest,
    InvoiceCreate,
    InvoiceRead,
    InvoiceUpdate,
)
from app.services import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def create_invoice(data: InvoiceCreate, db: Session = Depends(get_db)) -> InvoiceRead:
    return InvoiceService(db).create(data)


@router.post("/build", response_model=InvoiceRead, status_code=status.HTTP_201_CREATED)
def build_invoice(data: InvoiceBuildRequest, db: Session = Depends(get_db)) -> InvoiceRead:
    """Згенерувати інвойс з оплачуваних незабілених годин клієнта."""
    return InvoiceService(db).build_from_time_entries(data)


@router.get("", response_model=list[InvoiceRead])
def list_invoices(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[InvoiceRead]:
    return InvoiceService(db).list(offset=offset, limit=limit)


@router.get("/{invoice_id}", response_model=InvoiceRead)
def get_invoice(invoice_id: int, db: Session = Depends(get_db)) -> InvoiceRead:
    return InvoiceService(db).get(invoice_id)


@router.patch("/{invoice_id}", response_model=InvoiceRead)
def update_invoice(
    invoice_id: int, data: InvoiceUpdate, db: Session = Depends(get_db)
) -> InvoiceRead:
    return InvoiceService(db).update(invoice_id, data)


@router.delete("/{invoice_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_invoice(invoice_id: int, db: Session = Depends(get_db)) -> None:
    InvoiceService(db).delete(invoice_id)
