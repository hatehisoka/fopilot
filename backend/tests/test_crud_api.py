"""Integration tests for the CRUD API and its non-trivial invoice rules."""

from fastapi.testclient import TestClient


def _make_client(client: TestClient, **overrides) -> dict:
    payload = {
        "name": "Acme LLC",
        "country": "USA",
        "default_currency": "usd",  # lower case on purpose (normalization check)
        "payment_terms_days": 14,
        **overrides,
    }
    resp = client.post("/clients", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def _make_project(client: TestClient, client_id: int, **overrides) -> dict:
    payload = {
        "client_id": client_id,
        "name": "Backend",
        "hourly_rate": "50.00",
        "currency": "USD",
        **overrides,
    }
    resp = client.post("/projects", json=payload)
    assert resp.status_code == 201, resp.text
    return resp.json()


def test_client_crud_roundtrip(client: TestClient) -> None:
    created = _make_client(client)
    assert created["default_currency"] == "USD"  # normalized to upper case

    client_id = created["id"]
    assert client.get(f"/clients/{client_id}").json()["name"] == "Acme LLC"

    updated = client.patch(f"/clients/{client_id}", json={"name": "Acme Inc"})
    assert updated.status_code == 200
    assert updated.json()["name"] == "Acme Inc"

    assert len(client.get("/clients").json()) == 1

    assert client.delete(f"/clients/{client_id}").status_code == 204
    assert client.get(f"/clients/{client_id}").status_code == 404


def test_get_missing_client_returns_404(client: TestClient) -> None:
    assert client.get("/clients/999").status_code == 404


def test_project_requires_existing_client(client: TestClient) -> None:
    resp = client.post(
        "/projects",
        json={"client_id": 999, "name": "X", "hourly_rate": "10", "currency": "USD"},
    )
    assert resp.status_code == 404


def test_time_entry_requires_existing_project(client: TestClient) -> None:
    resp = client.post(
        "/time-entries",
        json={"project_id": 999, "work_date": "2026-01-01", "hours": "8"},
    )
    assert resp.status_code == 404


def test_invoice_due_date_derived_from_payment_terms(client: TestClient) -> None:
    c = _make_client(client, payment_terms_days=30)
    resp = client.post(
        "/invoices",
        json={
            "client_id": c["id"],
            "number": "INV-001",
            "issue_date": "2026-01-10",
            "currency": "USD",
            "items": [{"description": "Consulting", "quantity": "10", "unit_price": "50"}],
        },
    )
    assert resp.status_code == 201, resp.text
    body = resp.json()
    assert body["due_date"] == "2026-02-09"  # 2026-01-10 + 30 days
    assert body["amount"] == "500.00"


def test_invoice_number_must_be_unique(client: TestClient) -> None:
    c = _make_client(client)
    base = {
        "client_id": c["id"],
        "number": "INV-DUP",
        "issue_date": "2026-01-10",
        "currency": "USD",
    }
    assert client.post("/invoices", json=base).status_code == 201
    assert client.post("/invoices", json=base).status_code == 409


def test_double_billing_same_time_entry_is_conflict(client: TestClient) -> None:
    c = _make_client(client)
    p = _make_project(client, c["id"])
    te = client.post(
        "/time-entries",
        json={"project_id": p["id"], "work_date": "2026-01-02", "hours": "8"},
    ).json()

    first = client.post(
        "/invoices",
        json={
            "client_id": c["id"],
            "number": "INV-A",
            "issue_date": "2026-01-10",
            "currency": "USD",
            "items": [
                {
                    "time_entry_id": te["id"],
                    "description": "Dev",
                    "quantity": "8",
                    "unit_price": "50",
                }
            ],
        },
    )
    assert first.status_code == 201, first.text

    # Billing the same time entry into a second invoice must be rejected by the
    # DB-level partial unique index (ADR-004), surfaced as 409.
    second = client.post(
        "/invoices",
        json={
            "client_id": c["id"],
            "number": "INV-B",
            "issue_date": "2026-01-11",
            "currency": "USD",
            "items": [
                {
                    "time_entry_id": te["id"],
                    "description": "Dev again",
                    "quantity": "8",
                    "unit_price": "50",
                }
            ],
        },
    )
    assert second.status_code == 409, second.text
