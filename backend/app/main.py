"""FastAPI application entry point."""

from fastapi import FastAPI

app = FastAPI(title="FOPilot", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    """Liveness probe used by Docker Compose and CI."""
    return {"status": "ok"}
