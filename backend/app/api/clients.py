"""Client CRUD endpoints."""

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.db import get_db
from app.schemas import ClientCreate, ClientRead, ClientUpdate
from app.services import ClientService

router = APIRouter(prefix="/clients", tags=["clients"])


@router.post("", response_model=ClientRead, status_code=status.HTTP_201_CREATED)
def create_client(data: ClientCreate, db: Session = Depends(get_db)) -> ClientRead:
    return ClientService(db).create(data)


@router.get("", response_model=list[ClientRead])
def list_clients(
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
) -> list[ClientRead]:
    return ClientService(db).list(offset=offset, limit=limit)


@router.get("/{client_id}", response_model=ClientRead)
def get_client(client_id: int, db: Session = Depends(get_db)) -> ClientRead:
    return ClientService(db).get(client_id)


@router.patch("/{client_id}", response_model=ClientRead)
def update_client(client_id: int, data: ClientUpdate, db: Session = Depends(get_db)) -> ClientRead:
    return ClientService(db).update(client_id, data)


@router.delete("/{client_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_client(client_id: int, db: Session = Depends(get_db)) -> None:
    ClientService(db).delete(client_id)
