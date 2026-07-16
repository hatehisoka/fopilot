"""initial schema

Revision ID: 4b6efe947d50
Revises:
Create Date: 2026-07-16

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "4b6efe947d50"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "bank_transaction",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("tx_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("counterparty", sa.String(length=200), nullable=True),
        sa.Column("row_hash", sa.String(length=64), nullable=False),
        sa.Column("import_batch_id", sa.String(length=64), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("row_hash"),
    )
    op.create_table(
        "client",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("default_currency", sa.String(length=3), nullable=False),
        sa.Column("payment_terms_days", sa.Integer(), nullable=False),
        sa.Column("contacts", sa.String(length=500), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "exchange_rate",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("rate_date", sa.Date(), nullable=False),
        sa.Column("rate", sa.Numeric(precision=14, scale=6), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("currency", "rate_date", name="uq_exchange_rate_currency_date"),
    )
    op.create_table(
        "invoice",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("number", sa.String(length=50), nullable=False),
        sa.Column("issue_date", sa.Date(), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.Enum("draft", "sent", "paid", "partial", "overdue", name="invoice_status"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("number"),
    )
    op.create_table(
        "project",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("client_id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("hourly_rate", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column(
            "status",
            sa.Enum("active", "paused", "closed", name="project_status"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["client_id"], ["client.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "payment",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=True),
        sa.Column("bank_transaction_id", sa.Integer(), nullable=True),
        sa.Column("paid_date", sa.Date(), nullable=False),
        sa.Column("amount", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("currency", sa.String(length=3), nullable=False),
        sa.Column("amount_uah", sa.Numeric(precision=14, scale=2), nullable=True),
        sa.Column("source", sa.String(length=200), nullable=True),
        sa.Column(
            "match_status",
            sa.Enum(
                "unmatched",
                "auto",
                "needs_review",
                "confirmed",
                "rejected",
                name="match_status",
            ),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["bank_transaction_id"], ["bank_transaction.id"], ondelete="SET NULL"
        ),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "time_entry",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("work_date", sa.Date(), nullable=False),
        sa.Column("hours", sa.Numeric(precision=6, scale=2), nullable=False),
        sa.Column("description", sa.String(length=500), nullable=True),
        sa.Column("billable", sa.Boolean(), nullable=False),
        sa.ForeignKeyConstraint(["project_id"], ["project.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "invoice_item",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("invoice_id", sa.Integer(), nullable=False),
        sa.Column("time_entry_id", sa.Integer(), nullable=True),
        sa.Column("description", sa.String(length=500), nullable=False),
        sa.Column("quantity", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.Column("unit_price", sa.Numeric(precision=12, scale=2), nullable=False),
        sa.ForeignKeyConstraint(["invoice_id"], ["invoice.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["time_entry_id"], ["time_entry.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    # Partial unique index enforcing "no double billing" (see ADR-004).
    op.create_index(
        "uq_invoice_item_time_entry",
        "invoice_item",
        ["time_entry_id"],
        unique=True,
        postgresql_where=sa.text("time_entry_id IS NOT NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_invoice_item_time_entry",
        table_name="invoice_item",
        postgresql_where=sa.text("time_entry_id IS NOT NULL"),
    )
    op.drop_table("invoice_item")
    op.drop_table("time_entry")
    op.drop_table("payment")
    op.drop_table("project")
    op.drop_table("invoice")
    op.drop_table("exchange_rate")
    op.drop_table("client")
    op.drop_table("bank_transaction")
    # Postgres ENUM types are not dropped with their tables — drop explicitly so a
    # downgrade/upgrade cycle does not fail on "type already exists".
    sa.Enum(name="match_status").drop(op.get_bind())
    sa.Enum(name="invoice_status").drop(op.get_bind())
    sa.Enum(name="project_status").drop(op.get_bind())
