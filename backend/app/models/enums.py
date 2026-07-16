"""Enumerations shared across ORM models."""

import enum


class ProjectStatus(enum.StrEnum):
    active = "active"
    paused = "paused"
    closed = "closed"


class InvoiceStatus(enum.StrEnum):
    draft = "draft"
    sent = "sent"
    paid = "paid"
    partial = "partial"
    overdue = "overdue"


class MatchStatus(enum.StrEnum):
    """Lifecycle of a payment's link to an invoice (see ADR-002)."""

    unmatched = "unmatched"
    auto = "auto"
    needs_review = "needs_review"
    confirmed = "confirmed"
    rejected = "rejected"
