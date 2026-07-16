"""Bank statement import result schemas."""

from pydantic import BaseModel


class ImportRowError(BaseModel):
    row: int  # 1-based line number in the file (header = line 1)
    message: str


class ImportReport(BaseModel):
    profile: str
    added: int
    duplicates: int
    errors: int
    error_details: list[ImportRowError]
