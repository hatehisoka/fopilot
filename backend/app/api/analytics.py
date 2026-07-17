"""Analytics endpoints backing the dashboard."""

from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import (
    ConcentrationReport,
    EpForecast,
    ReceiptsReport,
    UtilizationReport,
)
from app.services import AnalyticsService

router = APIRouter(prefix="/analytics", tags=["analytics"])


@router.get("/receipts", response_model=ReceiptsReport)
def receipts(
    granularity: str = Query("month", pattern="^(month|quarter)$"),
    year: int | None = Query(None),
    db: Session = Depends(get_db),
) -> ReceiptsReport:
    """Надходження (касовий метод) по місяцях або кварталах."""
    return AnalyticsService(db).receipts_by_period(granularity=granularity, year=year)


@router.get("/utilization", response_model=UtilizationReport)
def utilization(
    date_from: date = Query(...),
    date_to: date = Query(...),
    db: Session = Depends(get_db),
) -> UtilizationReport:
    """Utilization: білабельні години до ємності (робочі дні × годин/день)."""
    return AnalyticsService(db).utilization(date_from, date_to)


@router.get("/concentration", response_model=ConcentrationReport)
def concentration(
    year: int | None = Query(None),
    db: Session = Depends(get_db),
) -> ConcentrationReport:
    """Концентрація доходу по клієнтах (частка топ-клієнта як ризик)."""
    return AnalyticsService(db).concentration(year=year)


@router.get("/ep-forecast", response_model=EpForecast)
def ep_forecast(
    year: int | None = Query(None),
    as_of: date | None = Query(None),
    db: Session = Depends(get_db),
) -> EpForecast:
    """Прогноз досягнення річного ліміту ЄП через run-rate (касовий метод)."""
    return AnalyticsService(db).ep_forecast(year=year, as_of=as_of)
