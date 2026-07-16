"""TimeEntry repository."""

from sqlalchemy.orm import Session

from app.models import TimeEntry
from app.repositories.base import BaseRepository


class TimeEntryRepository(BaseRepository[TimeEntry]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, TimeEntry)
