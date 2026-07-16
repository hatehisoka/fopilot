"""TimeEntry business logic."""

from sqlalchemy.orm import Session

from app.models import Project, TimeEntry
from app.repositories import TimeEntryRepository
from app.schemas import TimeEntryCreate, TimeEntryUpdate
from app.services.exceptions import NotFoundError


class TimeEntryService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = TimeEntryRepository(db)

    def get(self, entry_id: int) -> TimeEntry:
        entry = self.repo.get(entry_id)
        if entry is None:
            raise NotFoundError(f"Запис годин з id={entry_id} не знайдено")
        return entry

    def list(self, offset: int = 0, limit: int = 100) -> list[TimeEntry]:
        return self.repo.list(offset=offset, limit=limit)

    def create(self, data: TimeEntryCreate) -> TimeEntry:
        self._require_project(data.project_id)
        entry = TimeEntry(**data.model_dump())
        self.repo.add(entry)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def update(self, entry_id: int, data: TimeEntryUpdate) -> TimeEntry:
        entry = self.get(entry_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(entry, field, value)
        self.db.commit()
        self.db.refresh(entry)
        return entry

    def delete(self, entry_id: int) -> None:
        entry = self.get(entry_id)
        self.repo.delete(entry)
        self.db.commit()

    def _require_project(self, project_id: int) -> None:
        if self.db.get(Project, project_id) is None:
            raise NotFoundError(f"Проєкт з id={project_id} не знайдено")
