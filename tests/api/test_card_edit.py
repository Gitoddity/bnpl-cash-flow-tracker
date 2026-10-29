import json
import sqlite3
from datetime import date

from fastapi.testclient import TestClient
from bnpl_cashflow.api.app import create_app


def test_correcting_statement_dates_accepts_later_due_date(tmp_path):
    client = TestClient(create_app(tmp_path / 'dates.sqlite3'))
    profile = client.post('/api/profiles', json={'name': 'Sample'}).json()
    endpoint = f'/api/profiles/{profile["id"]}/cards'
    draft = {'name': 'Tvdya', 'current_balance': '500',
             'upcoming_statement_close_date': '2026-10-15',
             'upcoming_statement_due_date': '2026-10-10'}
    assert client.post(endpoint, json=draft).status_code == 422
    assert client.get(endpoint).json() == []
    draft['upcoming_statement_due_date'] = '2026-10-30'
    response = client.post(endpoint, json=draft)
    assert response.status_code == 201, response.text
    card = response.json()
    assert card['latest_statement_close_date'] == '2026-10-15'
    assert card['latest_statement_due_date'] == '2026-10-30'
    edit = endpoint + '/' + card['id']
    assert client.patch(edit, json={'upcoming_statement_due_date': '2026-10-01'}).status_code == 422
    assert client.patch(edit, json={'upcoming_statement_due_date': '2026-10-30'}).status_code == 200


def test_edit_preserves_identity_plans_and_other_profiles(tmp_path):
    path = tmp_path / 'profiles.sqlite3'
    client = TestClient(create_app(path, today_provider=lambda: date(2026, 9, 24)))
    source = {
        'format': 'bnpl-profile', 'version': 1, 'profile': {'id': 'personal', 'name': 'Personal'},
        'credit_cards': [{'id': 'card1', 'profile_id': 'personal', 'name': 'Card', 'current_balance': '100.00',
                          'current_balance_due_date': '2026-10-12', 'statement_end_day': 18, 'payment_due_day': 12}],
        'bnpl_plans': [{'id': 'plan1', 'plan_name': 'Purchase', 'provider_name': 'Klarna', 'purchase_amount': '120.00',
                        'currency': 'CAD', 'purchase_date': '2026-09-01', 'first_installment_date': '2026-09-01',
                        'installment_count': 4, 'installment_frequency': 'BIWEEKLY', 'credit_card_id': 'card1'}],
    }
    assert client.post('/api/profiles/import', json=source).status_code == 201
    with sqlite3.connect(path) as connection:
        original = json.loads(connection.execute('SELECT document FROM profiles WHERE id = ?', ('personal',)).fetchone()[0])
    other = client.post('/api/profiles', json={'name': 'Travel'}).json()
    url = '/api/profiles/personal/cards/card1'
    before = client.get('/api/profiles/personal/cards').json()
    for invalid in [{'payment_due_day': '32'}, {'name': ' '}, {'current_balance': '-1'}, {'statement_end_day': '0'}, {'card_number': 'forbidden'}, {'profile_id': other['id']}, {'id': 'replacement'}]:
        assert client.patch(url, json=invalid).status_code == 422
        assert client.get('/api/profiles/personal/cards').json() == before
    assert client.patch(f'/api/profiles/{other["id"]}/cards/card1', json={'name': 'No'}).status_code == 404
    assert client.patch('/api/profiles/personal/cards/missing', json={'name': 'No'}).status_code == 404
    result = client.patch(url, json={'name': 'Corrected', 'current_balance': '25.50', 'statement_end_day': '6', 'payment_due_day': '27'})
    assert result.status_code == 200
    assert result.json()['id'] == 'card1'
    assert result.json()['profile_id'] == 'personal'
    assert result.json()['next_statement_close_date'] == '2026-10-06'
    assert result.json()['next_payment_due_date'] == '2026-09-27'
    restored = TestClient(create_app(path)).get('/api/profiles/personal/cards').json()
    assert len(restored) == 1
    assert restored[0]['name'] == 'Corrected'
    assert restored[0]['current_balance'] == '25.50'
    with sqlite3.connect(path) as connection:
        stored = json.loads(connection.execute('SELECT document FROM profiles WHERE id = ?', ('personal',)).fetchone()[0])
    assert stored['bnpl_plans'] == original['bnpl_plans']
    assert stored['credit_cards'][0]['current_balance_due_date'] == '2026-10-12'
    assert client.get(f'/api/profiles/{other["id"]}/cards').json() == []
