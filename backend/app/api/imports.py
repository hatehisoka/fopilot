"""Bank statement import endpoint."""

from fastapi import APIRouter, Depends, File, Query, UploadFile
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ImportReport
from app.services import CsvImportService

router = APIRouter(prefix="/imports", tags=["imports"])


@router.post("/bank-statement", response_model=ImportReport)
async def import_bank_statement(
    profile: str = Query(..., description="Назва YAML-профілю банку"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
) -> ImportReport:
    """Імпортувати банківську виписку з CSV за вказаним профілем."""
    content = await file.read()
    return CsvImportService(db).import_file(content, profile)
