"""Project CRUD endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ProjectCreate, ProjectRead, ProjectUpdate
from app.services import ProjectService

router = APIRouter(prefix="/projects", tags=["projects"])


@router.post("", response_model=ProjectRead, status_code=status.HTTP_201_CREATED)
def create_project(data: ProjectCreate, db: Session = Depends(get_db)) -> ProjectRead:
    return ProjectService(db).create(data)


@router.get("", response_model=list[ProjectRead])
def list_projects(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ProjectRead]:
    return ProjectService(db).list(offset=offset, limit=limit)


@router.get("/{project_id}", response_model=ProjectRead)
def get_project(project_id: int, db: Session = Depends(get_db)) -> ProjectRead:
    return ProjectService(db).get(project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
def update_project(
    project_id: int, data: ProjectUpdate, db: Session = Depends(get_db)
) -> ProjectRead:
    return ProjectService(db).update(project_id, data)


@router.delete("/{project_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_project(project_id: int, db: Session = Depends(get_db)) -> None:
    ProjectService(db).delete(project_id)
