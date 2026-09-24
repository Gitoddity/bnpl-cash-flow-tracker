from copy import deepcopy
import json

import pytest
from fastapi.testclient import TestClient

from bnpl_cashflow.api.app import MAX_IMPORT_BYTES, create_app
from bnpl_cashflow.input import InputValidationError, parse_json_payload


@pytest.fixture
def client(tmp_path):
    return TestClient(create_app(tmp_path / "profiles.sqlite3"))


def document():
    return {
        "format": "bnpl-profile", "version": 1,
        "profile": {"id": "personal", "name": "Personal"},
        "credit_cards": [{"id": "card1", "name": "Card", "profile_id": "personal",
                          "statement_end_day": 13, "payment_due_day": 13, "current_balance": "10.00"}],
        "bnpl_plans": [{"id": "plan1", "plan_name": "Purchase", "provider_name": "Provider",
                        "purchase_amount": "120.00", "currency": "CAD", "purchase_date": "2026-09-01",
                        "first_installment_date": "2026-09-01", "installment_count": 4,
                        "installment_frequency": "BIWEEKLY", "credit_card_id": "card1"}],
    }


def test_create_persist_and_reject_duplicate(tmp_path):
    path = tmp_path / "profiles.sqlite3"
    client = TestClient(create_app(path))
    response = client.post("/api/profiles", json={"name": " Personal "})
    assert response.status_code == 201
    assert response.json()["name"] == "Personal"
    assert response.json()["card_count"] == 0
    assert TestClient(create_app(path)).get("/api/profiles").json() == [response.json()]
    assert client.post("/api/profiles", json={"name": "personal"}).status_code == 409
    assert client.post("/api/profiles", json={"name": "  "}).status_code == 422


def test_import_and_conflicts_do_not_overwrite(client):
    source = document()
    response = client.post("/api/profiles/import", json=source)
    assert response.status_code == 201
    assert response.json() == {"id": "personal", "name": "Personal", "card_count": 1, "plan_count": 1}
    same_id = deepcopy(source)
    same_id["profile"]["name"] = "Different"
    assert client.post("/api/profiles/import", json=same_id).status_code == 409
    same_name = deepcopy(source)
    same_name["profile"]["id"] = "another"
    same_name["credit_cards"][0]["profile_id"] = "another"
    assert client.post("/api/profiles/import", json=same_name).status_code == 409
    assert client.get("/api/profiles").json() == [response.json()]


@pytest.mark.parametrize("cards", [False, True])
def test_setup_profiles_can_import_without_plans(client, cards):
    source = document()
    source["bnpl_plans"] = []
    if not cards:
        source["credit_cards"] = []
    assert client.post("/api/profiles/import", json=source).status_code == 201
    # The calculation contract still rejects incomplete setup payloads.
    with pytest.raises(InputValidationError):
        parse_json_payload({"credit_cards": source["credit_cards"], "bnpl_plans": []})


@pytest.mark.parametrize("mutation", [
    lambda d: d.update(version=2),
    lambda d: d.update(version=True),
    lambda d: d.update(format="workspace-draft"),
    lambda d: d.update(profiles=[]),
    lambda d: d["profile"].update(name=" "),
    lambda d: d["credit_cards"][0].update(profile_id="someone-else"),
    lambda d: d["credit_cards"][0].update(card_number="4111111111111111"),
    lambda d: d["credit_cards"][0].update(statement_end_day=32),
    lambda d: d["credit_cards"][0].update(current_balance="NaN"),
    lambda d: d["bnpl_plans"][0].update(purchase_amount="Infinity"),
    lambda d: d["bnpl_plans"][0].update(purchase_amount="-1"),
    lambda d: d["bnpl_plans"][0].update(credit_card_id="missing"),
    lambda d: d.update(credit_cards=[]),
    lambda d: d["bnpl_plans"].append(deepcopy(d["bnpl_plans"][0])),
    lambda d: d["credit_cards"].append(deepcopy(d["credit_cards"][0])),
    lambda d: d["bnpl_plans"].append({**d["bnpl_plans"][0], "id": "plan2", "currency": "USD"}),
])
def test_invalid_imports_never_write(client, mutation):
    source = document()
    mutation(source)
    assert client.post("/api/profiles/import", json=source).status_code == 422
    assert client.get("/api/profiles").json() == []


def test_json_and_size_errors(client):
    for content in ('{', '{"version":1,"version":2}', 'NaN', 'null', '[]'):
        assert client.post("/api/profiles/import", content=content,
                           headers={"Content-Type": "application/json"}).status_code == 422
    assert client.post("/api/profiles/import", content=b" " * (MAX_IMPORT_BYTES + 1),
                       headers={"Content-Type": "application/json"}).status_code == 413
    assert client.post("/api/profiles/import", content="{}").status_code == 415


def test_utf8_bom_and_canonical_storage(tmp_path):
    import sqlite3
    path = tmp_path / "profiles.sqlite3"
    client = TestClient(create_app(path))
    source = document()
    source["bnpl_plans"][0]["currency"] = "cad"
    response = client.post("/api/profiles/import", content=b"\xef\xbb\xbf" + json.dumps(source).encode(),
                           headers={"Content-Type": "application/json"})
    assert response.status_code == 201
    with sqlite3.connect(path) as connection:
        stored = json.loads(connection.execute("SELECT document FROM profiles").fetchone()[0])
    assert stored["bnpl_plans"][0]["currency"] == "CAD"
    assert stored["bnpl_plans"][0]["purchase_amount"] == "120.00"
    assert client.post("/api/profiles/import", json=stored).status_code == 409
