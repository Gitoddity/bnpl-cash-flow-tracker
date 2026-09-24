import json
import sqlite3
from datetime import date
from concurrent.futures import ThreadPoolExecutor

import pytest
from fastapi.testclient import TestClient

from bnpl_cashflow.api.app import create_app


def draft(**changes):
    return {"name": " TD Visa ", "current_balance": "500.00",
            "statement_end_day": "18", "payment_due_day": "12", **changes}


@pytest.fixture
def setup(tmp_path):
    path = tmp_path / "profiles.sqlite3"
    client = TestClient(create_app(path))
    profile = client.post("/api/profiles", json={"name": "Personal"}).json()
    return client, f'/api/profiles/{profile["id"]}/cards', path, profile["id"]


def test_card_saved_under_active_profile_and_survives_restart(setup):
    client, url, path, profile_id = setup
    other = client.post("/api/profiles", json={"name": "Travel"}).json()
    response = client.post(url, json=draft())
    assert response.status_code == 201
    card = response.json()
    assert {key: value for key, value in card.items() if key not in {'as_of_date', 'next_statement_close_date', 'next_payment_due_date'}} == {"id": card["id"], "profile_id": profile_id, "name": "TD Visa",
                    "current_balance": "500.00", "statement_end_day": 18, "payment_due_day": 12}
    assert TestClient(create_app(path)).get(url).json() == [card]
    assert client.get(f'/api/profiles/{other["id"]}/cards').json() == []
    assert next(p for p in client.get('/api/profiles').json() if p['id'] == profile_id)['card_count'] == 1
    assert client.get('/api/profiles/missing/cards').status_code == 404
    assert client.post('/api/profiles/missing/cards', json=draft()).status_code == 404


@pytest.mark.parametrize('changes,field', [
    ({'name': '  '}, 'name'), ({'name': None}, 'name'),
    ({'current_balance': '-0.01'}, 'current_balance'),
    ({'current_balance': ''}, 'current_balance'),
    ({'current_balance': 'NaN'}, 'current_balance'),
    ({'current_balance': 'Infinity'}, 'current_balance'),
    ({'current_balance': 'not money'}, 'current_balance'),
    ({'current_balance': 500}, 'current_balance'),
    ({'statement_end_day': '0'}, 'statement_end_day'),
    ({'statement_end_day': '32'}, 'statement_end_day'),
    ({'statement_end_day': '1.5'}, 'statement_end_day'),
    ({'payment_due_day': '-1'}, 'payment_due_day'),
    ({'payment_due_day': '32'}, 'payment_due_day'),
    ({'payment_due_day': True}, 'payment_due_day'),
])
def test_shared_validation_reports_fields_without_writing(setup, changes, field):
    client, url, _, _ = setup
    response = client.post(url, json=draft(**changes))
    assert response.status_code == 422
    assert f'credit_cards[0].{field}' in [issue['path'] for issue in response.json()['issues']]
    assert client.get(url).json() == []


def test_missing_nickname_and_boundary_days(setup):
    client, url, _, _ = setup
    body = draft()
    del body['name']
    assert client.post(url, json=body).json()['issues'][0]['path'] == 'credit_cards[0].name'
    for close, due in [(31, 1), (1, 31), (18, 18)]:
        assert client.post(url, json=draft(statement_end_day=close, payment_due_day=due)).status_code == 201


@pytest.mark.parametrize('unsupported', ['cardholder_name', 'card_number', 'last_four', 'expiry_date',
    'cvv', 'pin', 'banking_login', 'password', 'apr', 'network', 'credit_limit', 'profile_id', 'id'])
def test_credentials_and_ownership_overrides_are_never_stored(setup, unsupported):
    client, url, path, _ = setup
    assert client.post(url, json=draft(**{unsupported: 'do-not-store-this'})).status_code == 422
    with sqlite3.connect(path) as connection:
        stored = connection.execute('SELECT document FROM profiles').fetchone()[0]
    assert 'do-not-store-this' not in stored
    assert json.loads(stored)['credit_cards'] == []


def test_concurrent_additions_preserve_every_card(setup):
    client, url, _, _ = setup
    with ThreadPoolExecutor(max_workers=4) as executor:
        responses = list(executor.map(lambda index: client.post(url, json=draft(name=f'Card {index}')), range(4)))
    assert all(response.status_code == 201 for response in responses)
    cards = client.get(url).json()
    assert {card['name'] for card in cards} == {f'Card {index}' for index in range(4)}
    assert len({card['id'] for card in cards}) == 4


@pytest.mark.parametrize('as_of,closing,due,next_close,next_due', [
    ('2026-09-24', 18, 12, '2026-10-18', '2026-10-12'),
    ('2026-10-12', 18, 12, '2026-10-18', '2026-10-12'),
    ('2026-10-13', 18, 12, '2026-10-18', '2026-11-12'),
    ('2026-10-18', 18, 12, '2026-10-18', '2026-11-12'),
    ('2026-12-31', 18, 12, '2027-01-18', '2027-01-12'),
    ('2026-12-18', 18, 12, '2026-12-18', '2027-01-12'),
    ('2026-09-24', 6, 27, '2026-10-06', '2026-09-27'),
    ('2026-02-27', 31, 31, '2026-02-28', '2026-02-28'),
    ('2028-02-29', 31, 31, '2028-02-29', '2028-02-29'),
    ('2026-10-18', 18, 18, '2026-10-18', '2026-10-18'),
])
def test_upcoming_dates_use_application_clock_and_survive_reload(tmp_path, as_of, closing, due, next_close, next_due):
    path = tmp_path / 'profiles.sqlite3'
    client = TestClient(create_app(path, today_provider=lambda: date.fromisoformat(as_of)))
    profile = client.post('/api/profiles', json={'name': 'Personal'}).json()
    url = f'/api/profiles/{profile["id"]}/cards'
    response = client.post(url, json=draft(statement_end_day=closing, payment_due_day=due))
    assert response.status_code == 201
    card = response.json()
    assert card['as_of_date'] == as_of
    assert card['next_statement_close_date'] == next_close
    assert card['next_payment_due_date'] == next_due
    assert client.get(url).json() == [card]
    with sqlite3.connect(path) as connection:
        stored = json.loads(connection.execute('SELECT document FROM profiles').fetchone()[0])
    assert 'as_of_date' not in stored['credit_cards'][0]
    later = TestClient(create_app(path, today_provider=lambda: date(2029, 1, 1)))
    assert later.get(url).json()[0]['as_of_date'] == '2029-01-01'
    assert later.get(url).json()[0]['id'] == card['id']
