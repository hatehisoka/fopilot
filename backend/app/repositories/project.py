"""Project repository."""

from sqlalchemy.orm import Session

from app.models import Project
from app.repositories.base import BaseRepository


class ProjectRepository(BaseRepository[Project]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Project)
