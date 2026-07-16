"""TimeEntry CRUD endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import TimeEntryCreate, TimeEntryRead, TimeEntryUpdate
from app.services import TimeEntryService

router = APIRouter(prefix="/time-entries", tags=["time-entries"])


@router.post("", response_model=TimeEntryRead, status_code=status.HTTP_201_CREATED)
def create_time_entry(data: TimeEntryCreate, db: Session = Depends(get_db)) -> TimeEntryRead:
    return TimeEntryService(db).create(data)


@router.get("", response_model=list[TimeEntryRead])
def list_time_entries(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[TimeEntryRead]:
    return TimeEntryService(db).list(offset=offset, limit=limit)


@router.get("/{entry_id}", response_model=TimeEntryRead)
def get_time_entry(entry_id: int, db: Session = Depends(get_db)) -> TimeEntryRead:
    return TimeEntryService(db).get(entry_id)


@router.patch("/{entry_id}", response_model=TimeEntryRead)
def update_time_entry(
    entry_id: int, data: TimeEntryUpdate, db: Session = Depends(get_db)
) -> TimeEntryRead:
    return TimeEntryService(db).update(entry_id, data)


@router.delete("/{entry_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_time_entry(entry_id: int, db: Session = Depends(get_db)) -> None:
    TimeEntryService(db).delete(entry_id)
