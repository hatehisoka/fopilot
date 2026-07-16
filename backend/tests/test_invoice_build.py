"""Tests for building invoices from billable time entries (ADR-011)."""

from fastapi.testclient import TestClient


def _client(client: TestClient, currency: str = "USD") -> int:
    resp = client.post(
        "/clients",
        json={"name": "Globex", "default_currency": currency, "payment_terms_days": 20},
    )
    return resp.json()["id"]


def _project(client: TestClient, client_id: int, rate: str, currency: str = "USD") -> int:
    resp = client.post(
        "/projects",
        json={
            "client_id": client_id,
            "name": "API work",
            "hourly_rate": rate,
            "currency": currency,
        },
    )
    return resp.json()["id"]


def _time_entry(
    client: TestClient, project_id: int, hours: str, day: str, billable: bool = True
) -> int:
    resp = client.post(
        "/time-entries",
        json={
            "project_id": project_id,
            "work_date": day,
            "hours": hours,
            "billable": billable,
        },
    )
    return resp.json()["id"]


def test_build_invoice_from_billable_hours(client: TestClient) -> None:
    client_id = _client(client)
    project_id = _project(client, client_id, rate="60")
    _time_entry(client, project_id, hours="8", day="2026-02-03")
    _time_entry(client, project_id, hours="5", day="2026-02-04")
    # Non-billable hours must be excluded from the invoice.
    _time_entry(client, project_id, hours="4", day="2026-02-05", billable=False)

    resp = client.post(
        "/invoices/build",
        json={"client_id": client_id, "number": "INV-B1", "issue_date": "2026-02-28"},
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()

    assert len(body["items"]) == 2  # only the two billable entries
    assert body["currency"] == "USD"  # derived from the project
    assert body["amount"] == "780.00"  # (8 + 5) * 60
    assert body["due_date"] == "2026-03-20"  # 2026-02-28 + 20 days


def test_built_hours_are_not_billed_twice(client: TestClient) -> None:
    client_id = _client(client)
    project_id = _project(client, client_id, rate="50")
    _time_entry(client, project_id, hours="8", day="2026-02-03")

    first = client.post(
        "/invoices/build",
        json={"client_id": client_id, "number": "INV-B2", "issue_date": "2026-02-28"},
    )
    assert first.status_code == 201

    # All hours are now billed — a second build has nothing to bill.
    second = client.post(
        "/invoices/build",
        json={"client_id": client_id, "number": "INV-B3", "issue_date": "2026-02-28"},
    )
    assert second.status_code == 409, second.text


def test_build_rejects_mixed_currencies(client: TestClient) -> None:
    client_id = _client(client)
    usd_project = _project(client, client_id, rate="50", currency="USD")
    eur_project = _project(client, client_id, rate="45", currency="EUR")
    _time_entry(client, usd_project, hours="8", day="2026-02-03")
    _time_entry(client, eur_project, hours="8", day="2026-02-03")

    resp = client.post(
        "/invoices/build",
        json={"client_id": client_id, "number": "INV-B4", "issue_date": "2026-02-28"},
    )
    assert resp.status_code == 409, resp.text


def test_build_with_no_hours_is_conflict(client: TestClient) -> None:
    client_id = _client(client)
    resp = client.post(
        "/invoices/build",
        json={"client_id": client_id, "number": "INV-B5", "issue_date": "2026-02-28"},
    )
    assert resp.status_code == 409


def test_build_respects_date_range(client: TestClient) -> None:
    client_id = _client(client)
    project_id = _project(client, client_id, rate="100")
    _time_entry(client, project_id, hours="8", day="2026-01-15")  # out of range
    _time_entry(client, project_id, hours="3", day="2026-02-10")  # in range

    resp = client.post(
        "/invoices/build",
        json={
            "client_id": client_id,
            "number": "INV-B6",
            "issue_date": "2026-02-28",
            "date_from": "2026-02-01",
            "date_to": "2026-02-28",
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert len(body["items"]) == 1
    assert body["amount"] == "300.00"  # only the 3h entry * 100
