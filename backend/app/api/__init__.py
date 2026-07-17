"""API layer: thin routers delegating to services."""

from fastapi import APIRouter

from app.api import (
    analytics,
    clients,
    imports,
    invoices,
    payments,
    projects,
    time_entries,
)

api_router = APIRouter()
api_router.include_router(clients.router)
api_router.include_router(projects.router)
api_router.include_router(time_entries.router)
api_router.include_router(invoices.router)
api_router.include_router(imports.router)
api_router.include_router(payments.router)
api_router.include_router(analytics.router)

__all__ = ["api_router"]
