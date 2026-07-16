"""Project business logic."""

from sqlalchemy.orm import Session

from app.models import Client, Project
from app.repositories import ProjectRepository
from app.schemas import ProjectCreate, ProjectUpdate
from app.services.exceptions import NotFoundError


class ProjectService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ProjectRepository(db)

    def get(self, project_id: int) -> Project:
        project = self.repo.get(project_id)
        if project is None:
            raise NotFoundError(f"Проєкт з id={project_id} не знайдено")
        return project

    def list(self, offset: int = 0, limit: int = 100) -> list[Project]:
        return self.repo.list(offset=offset, limit=limit)

    def create(self, data: ProjectCreate) -> Project:
        self._require_client(data.client_id)
        project = Project(**data.model_dump())
        self.repo.add(project)
        self.db.commit()
        self.db.refresh(project)
        return project

    def update(self, project_id: int, data: ProjectUpdate) -> Project:
        project = self.get(project_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        self.db.commit()
        self.db.refresh(project)
        return project

    def delete(self, project_id: int) -> None:
        project = self.get(project_id)
        self.repo.delete(project)
        self.db.commit()

    def _require_client(self, client_id: int) -> None:
        if self.db.get(Client, client_id) is None:
            raise NotFoundError(f"Клієнта з id={client_id} не знайдено")
