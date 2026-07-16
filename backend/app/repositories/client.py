"""Client repository."""

from sqlalchemy.orm import Session

from app.models import Client
from app.repositories.base import BaseRepository


class ClientRepository(BaseRepository[Client]):
    def __init__(self, db: Session) -> None:
        super().__init__(db, Client)
