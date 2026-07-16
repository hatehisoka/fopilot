"""Tests for the CSV bank statement import (encoding, formats, dedup, report)."""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models import BankTransaction
from app.services import CsvImportService
from app.services.exceptions import ConflictError, NotFoundError

FIXTURES = Path(__file__).parent / "fixtures"


def _fixture(name: str) -> bytes:
    return (FIXTURES / name).read_bytes()


def test_import_generic_utf8(db: Session) -> None:
    report = CsvImportService(db).import_file(_fixture("generic_utf8.csv"), "generic")

    assert report.added == 4  # 4 valid rows (incl. the two legit identical ones)
    assert report.duplicates == 0
    assert report.errors == 1
    assert report.error_details[0].row == 6  # the "bad-date" line
    assert "дата" in report.error_details[0].message.lower()


def test_legit_identical_rows_are_both_imported(db: Session) -> None:
    """Two identical rows in one file must survive (occurrence index, ADR-008)."""
    CsvImportService(db).import_file(_fixture("generic_utf8.csv"), "generic")

    count = db.scalar(
        select(func.count()).select_from(BankTransaction).where(BankTransaction.amount == 500)
    )
    assert count == 2


def test_reimport_same_file_is_deduplicated(db: Session) -> None:
    service = CsvImportService(db)
    service.import_file(_fixture("generic_utf8.csv"), "generic")

    second = service.import_file(_fixture("generic_utf8.csv"), "generic")
    assert second.added == 0
    assert second.duplicates == 4  # every valid row recognised as a duplicate
    assert second.errors == 1

    total = db.scalar(select(func.count()).select_from(BankTransaction))
    assert total == 4  # nothing added on the second pass


def test_import_windows1251_privatbank(db: Session) -> None:
    report = CsvImportService(db).import_file(_fixture("privatbank_win1251.csv"), "privatbank")
    assert report.added == 3
    assert report.errors == 0

    rows = db.scalars(select(BankTransaction).order_by(BankTransaction.tx_date)).all()
    # Cyrillic decoded correctly, "1 000,00" -> 1000.00, dd.mm.yyyy parsed.
    assert rows[0].description == "Оплата рахунку INV-010"
    assert rows[0].counterparty == "ТОВ Ромашка"
    assert str(rows[0].amount) == "1000.00"
    assert rows[0].tx_date.isoformat() == "2026-02-03"
    assert str(rows[2].amount) == "2500.75"  # space thousands separator handled


def test_missing_required_column_is_rejected(db: Session) -> None:
    content = b"date,currency,description\n2026-02-03,USD,no amount column\n"
    with pytest.raises(ConflictError):
        CsvImportService(db).import_file(content, "generic")


def test_unknown_profile_raises_not_found(db: Session) -> None:
    with pytest.raises(NotFoundError):
        CsvImportService(db).import_file(b"date,amount\n", "no_such_bank")


def test_import_endpoint_returns_report(client: TestClient) -> None:
    resp = client.post(
        "/imports/bank-statement",
        params={"profile": "generic"},
        files={"file": ("statement.csv", _fixture("generic_utf8.csv"), "text/csv")},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["profile"] == "generic"
    assert body["added"] == 4
    assert body["errors"] == 1
