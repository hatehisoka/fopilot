"""Client business logic."""

from sqlalchemy.orm import Session

from app.models import Client
from app.repositories import ClientRepository
from app.schemas import ClientCreate, ClientUpdate
from app.services.exceptions import NotFoundError


class ClientService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = ClientRepository(db)

    def get(self, client_id: int) -> Client:
        client = self.repo.get(client_id)
        if client is None:
            raise NotFoundError(f"Клієнта з id={client_id} не знайдено")
        return client

    def list(self, offset: int = 0, limit: int = 100) -> list[Client]:
        return self.repo.list(offset=offset, limit=limit)

    def create(self, data: ClientCreate) -> Client:
        client = Client(**data.model_dump())
        self.repo.add(client)
        self.db.commit()
        self.db.refresh(client)
        return client

    def update(self, client_id: int, data: ClientUpdate) -> Client:
        client = self.get(client_id)
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(client, field, value)
        self.db.commit()
        self.db.refresh(client)
        return client

    def delete(self, client_id: int) -> None:
        client = self.get(client_id)
        self.repo.delete(client)
        self.db.commit()
