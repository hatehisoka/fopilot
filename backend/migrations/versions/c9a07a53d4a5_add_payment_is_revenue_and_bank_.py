"""add payment.is_revenue and bank_transaction unique index

Revision ID: c9a07a53d4a5
Revises: cdda692e2582
Create Date: 2026-07-17

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "c9a07a53d4a5"
down_revision: str | None = "cdda692e2582"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # Revenue flag for the single-tax limit (ADR-012); defaults to true.
    op.add_column(
        "payment",
        sa.Column("is_revenue", sa.Boolean(), server_default=sa.text("true"), nullable=False),
    )
    # One bank row -> at most one payment; makes matching idempotent (ADR-013).
    op.create_index(
        "uq_payment_bank_transaction",
        "payment",
        ["bank_transaction_id"],
        unique=True,
        postgresql_where=sa.text("bank_transaction_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_payment_bank_transaction",
        table_name="payment",
        postgresql_where=sa.text("bank_transaction_id IS NOT NULL"),
    )
    op.drop_column("payment", "is_revenue")
