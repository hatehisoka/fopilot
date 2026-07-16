"""API layer: thin routers delegating to services."""

from fastapi import APIRouter

from app.api import clients, invoices, projects, time_entries

api_router = APIRouter()
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(time_entries.router)
api_router.include_router(invoices.router)

__all__ = ["api_router"]
