"""Shared pytest fixtures.

Integration tests run against a real Postgres test database (schema built by
Alembic migrations — no create_all, per project rules). If the database is not
reachable, the dependent tests are skipped rather than failing, so a machine
without Postgres can still run the pure-logic tests.
"""

import os
from collections.abc import Iterator

import pytest
from alembic import command
from alembic.config import Config
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from app.db import get_db
from app.main import app

TEST_DATABASE_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql+psycopg://localhost:5432/fopilot_test"
)

# Tables truncated between tests to isolate them (order irrelevant with CASCADE).
_TABLES = [
    "invoice_item",
    "payment",
    "time_entry",
    "invoice",
    "project",
    "bank_transaction",
    "exchange_rate",
    "client",
]


@pytest.fixture(scope="session")
def engine() -> Iterator[Engine]:
    eng = create_engine(TEST_DATABASE_URL)
    try:
        eng.connect().close()
    except Exception as exc:
        # Skip is a local convenience only. In CI (and anywhere FOPILOT_REQUIRE_DB
        # is set) an unreachable DB must FAIL, so the pipeline can never go green
        # on silently skipped integration tests.
        if os.environ.get("FOPILOT_REQUIRE_DB"):
            pytest.fail(f"Тестова БД недоступна, а FOPILOT_REQUIRE_DB заданий: {exc}")
        pytest.skip("Тестова БД недоступна", allow_module_level=False)

    cfg = Config("alembic.ini")
    cfg.set_main_option("sqlalchemy.url", TEST_DATABASE_URL)
    command.upgrade(cfg, "head")
    yield eng
    command.downgrade(cfg, "base")
    eng.dispose()


@pytest.fixture
def db(engine: Engine) -> Iterator[Session]:
    session_factory = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)
    session = session_factory()
    yield session
    session.rollback()
    with engine.begin() as conn:
        conn.execute(text(f"TRUNCATE {', '.join(_TABLES)} RESTART IDENTITY CASCADE"))
    session.close()


@pytest.fixture
def client(db: Session) -> Iterator[TestClient]:
    app.dependency_overrides[get_db] = lambda: db
    yield TestClient(app)
    app.dependency_overrides.clear()
