"""Generic repository with common CRUD data-access operations."""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import Base


class BaseRepository[ModelT: Base]:
    def __init__(self, db: Session, model: type[ModelT]) -> None:
        self.db = db
        self.model = model

    def get(self, entity_id: int) -> ModelT | None:
        return self.db.get(self.model, entity_id)

    def list(self, offset: int = 0, limit: int = 100) -> list[ModelT]:
        stmt = select(self.model).order_by(self.model.id).offset(offset).limit(limit)
        return list(self.db.scalars(stmt).all())

    def add(self, obj: ModelT) -> ModelT:
        self.db.add(obj)
        self.db.flush()
        return obj

    def delete(self, obj: ModelT) -> None:
        self.db.delete(obj)
        self.db.flush()
