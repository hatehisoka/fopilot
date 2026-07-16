"""add exchange_rate.source_date

Revision ID: cdda692e2582
Revises: 4b6efe947d50
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "cdda692e2582"
down_revision: str | None = "4b6efe947d50"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Provenance of a cached rate: NULL = published by NBU for rate_date,
    # a value = taken via fallback from that earlier banking day (ADR-006).
    op.add_column("exchange_rate", sa.Column("source_date", sa.Date(), nullable=True))


def downgrade() -> None:
    op.drop_column("exchange_rate", "source_date")
