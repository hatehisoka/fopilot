"""Bank statement CSV import.

Handles the messy parts of real statements: unknown encoding (UTF-8 /
Windows-1251, auto-detected), per-bank column mapping via YAML profiles, varied
date formats and decimal separators, and deterministic deduplication by a row
hash that includes the row's occurrence index within the file (ADR-008).
"""

import csv
import hashlib
import io
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from uuid import uuid4

import yaml
from charset_normalizer import from_bytes
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.models import BankTransaction
from app.repositories import BankTransactionRepository
from app.schemas import ImportReport, ImportRowError
from app.services.exceptions import ConflictError, NotFoundError

PROFILES_DIR = Path(__file__).resolve().parent.parent / "import_profiles"


class ColumnMapping(BaseModel):
    date: str
    amount: str
    currency: str | None = None
    description: str | None = None
    counterparty: str | None = None


class ImportProfile(BaseModel):
    name: str
    encoding: str | None = None
    delimiter: str = ","
    decimal_separator: str = "."
    thousands_separator: str | None = None
    date_formats: list[str]
    default_currency: str = "UAH"
    columns: ColumnMapping


@dataclass(frozen=True)
class ParsedRow:
    tx_date: date
    amount: Decimal
    currency: str
    description: str | None
    counterparty: str | None


def load_profile(name: str) -> ImportProfile:
    path = PROFILES_DIR / f"{name}.yaml"
    if not path.exists():
        raise NotFoundError(f"Профіль імпорту {name!r} не знайдено")
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return ImportProfile(**data)


def _decode(content: bytes, encoding: str | None) -> str:
    """Decode file bytes, auto-detecting the encoding when not pinned."""
    if encoding:
        text = content.decode(encoding)
    else:
        match = from_bytes(content).best()
        text = str(match) if match is not None else content.decode("utf-8", errors="replace")
    return text.lstrip("﻿")  # strip a leading BOM if present


def _parse_date(raw: str, formats: list[str]) -> date:
    value = raw.strip()
    for fmt in formats:
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            continue
    raise ValueError(f"некоректна дата {raw!r}")


def _parse_amount(raw: str, decimal_sep: str, thousands_sep: str | None) -> Decimal:
    s = raw.strip().replace("\xa0", "")  # drop non-breaking spaces
    if thousands_sep:
        s = s.replace(thousands_sep, "")
    s = s.replace(" ", "")  # plain spaces are never significant in a number
    if decimal_sep != ".":
        s = s.replace(decimal_sep, ".")
    try:
        return Decimal(s)
    except InvalidOperation as exc:
        raise ValueError(f"некоректна сума {raw!r}") from exc


class CsvImportService:
    def __init__(self, db: Session) -> None:
        self.db = db
        self.repo = BankTransactionRepository(db)

    def import_file(self, content: bytes, profile_name: str) -> ImportReport:
        profile = load_profile(profile_name)
        text = _decode(content, profile.encoding)
        reader = csv.DictReader(io.StringIO(text), delimiter=profile.delimiter)

        self._require_columns(reader.fieldnames, profile.columns)

        errors: list[ImportRowError] = []
        prepared: list[tuple[ParsedRow, str]] = []
        occurrences: dict[str, int] = {}

        # Header is line 1, so data rows start at line 2.
        for line_no, row in enumerate(reader, start=2):
            try:
                parsed = self._parse_row(row, profile)
            except ValueError as exc:
                errors.append(ImportRowError(row=line_no, message=str(exc)))
                continue
            base_key = self._base_key(parsed)
            occ = occurrences.get(base_key, 0)
            occurrences[base_key] = occ + 1
            row_hash = hashlib.sha256(f"{base_key}|{occ}".encode()).hexdigest()
            prepared.append((parsed, row_hash))

        existing = self.repo.existing_hashes([h for _, h in prepared])
        batch_id = uuid4().hex
        added = 0
        duplicates = 0
        for parsed, row_hash in prepared:
            if row_hash in existing:
                duplicates += 1
                continue
            existing.add(row_hash)
            self.db.add(
                BankTransaction(
                    tx_date=parsed.tx_date,
                    amount=parsed.amount,
                    currency=parsed.currency,
                    description=parsed.description,
                    counterparty=parsed.counterparty,
                    row_hash=row_hash,
                    import_batch_id=batch_id,
                )
            )
            added += 1

        self.db.commit()
        return ImportReport(
            profile=profile.name,
            added=added,
            duplicates=duplicates,
            errors=len(errors),
            error_details=errors,
        )

    @staticmethod
    def _require_columns(fieldnames: list[str] | None, columns: ColumnMapping) -> None:
        present = set(fieldnames or [])
        missing = [c for c in (columns.date, columns.amount) if c not in present]
        if missing:
            raise ConflictError(f"У файлі немає обов'язкових колонок: {missing}")

    @staticmethod
    def _parse_row(row: dict[str, str | None], profile: ImportProfile) -> ParsedRow:
        cols = profile.columns
        tx_date = _parse_date(row.get(cols.date) or "", profile.date_formats)
        amount = _parse_amount(
            row.get(cols.amount) or "", profile.decimal_separator, profile.thousands_separator
        )
        currency = (
            ((row.get(cols.currency) if cols.currency else None) or profile.default_currency)
            .strip()
            .upper()
        )
        description = _optional(row.get(cols.description) if cols.description else None)
        counterparty = _optional(row.get(cols.counterparty) if cols.counterparty else None)
        return ParsedRow(tx_date, amount, currency, description, counterparty)

    @staticmethod
    def _base_key(parsed: ParsedRow) -> str:
        return "|".join(
            [
                parsed.tx_date.isoformat(),
                str(parsed.amount),
                parsed.currency,
                parsed.description or "",
                parsed.counterparty or "",
            ]
        )


def _optional(value: str | None) -> str | None:
    if value is None:
        return None
    stripped = value.strip()
    return stripped or None
