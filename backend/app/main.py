"""FastAPI application entry point."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse

from app.api import api_router
from app.services import ConflictError, NotFoundError

app = FastAPI(title="FOPilot", version="0.1.0")


@app.exception_handler(NotFoundError)
def handle_not_found(request: Request, exc: NotFoundError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_404_NOT_FOUND, content={"detail": str(exc)})


@app.exception_handler(ConflictError)
def handle_conflict(request: Request, exc: ConflictError) -> JSONResponse:
    return JSONResponse(status_code=status.HTTP_409_CONFLICT, content={"detail": str(exc)})


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and CI."""
    return {"status": "ok"}


app.include_router(api_router)
