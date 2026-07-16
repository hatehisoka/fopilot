"""Payment endpoints: matching run, review list, confirm/reject, revenue flag."""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models.enums import MatchStatus
from app.schemas import (
    MatchRunReport,
    PaymentConfirm,
    PaymentRead,
    PaymentRevenueUpdate,
)
from app.services import MatchingService, PaymentService

router = APIRouter(prefix="/payments", tags=["payments"])


@router.post("/match", response_model=MatchRunReport)
def run_matching(db: Session = Depends(get_db)) -> MatchRunReport:
    """Згенерувати платежі з нових надходжень і зіставити з інвойсами."""
    return MatchingService(db).run()


@router.get("", response_model=list[PaymentRead])
def list_payments(
    match_status: MatchStatus | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[PaymentRead]:
    return PaymentService(db).list(match_status=match_status, offset=offset, limit=limit)


@router.get("/{payment_id}", response_model=PaymentRead)
def get_payment(payment_id: int, db: Session = Depends(get_db)) -> PaymentRead:
    return PaymentService(db).get(payment_id)


@router.post("/{payment_id}/confirm", response_model=PaymentRead)
def confirm_payment(
    payment_id: int, data: PaymentConfirm, db: Session = Depends(get_db)
) -> PaymentRead:
    """Підтвердити зіставлення платежу з інвойсом."""
    return PaymentService(db).confirm(payment_id, data.invoice_id)


@router.post("/{payment_id}/reject", response_model=PaymentRead)
def reject_payment(payment_id: int, db: Session = Depends(get_db)) -> PaymentRead:
    """Відхилити запропоноване зіставлення."""
    return PaymentService(db).reject(payment_id)


@router.patch("/{payment_id}/revenue", response_model=PaymentRead)
def set_payment_revenue(
    payment_id: int, data: PaymentRevenueUpdate, db: Session = Depends(get_db)
) -> PaymentRead:
    """Позначити платіж як дохідний / недохідний для ліміту ЄП."""
    return PaymentService(db).set_revenue(payment_id, data.is_revenue)
