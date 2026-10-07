import pytest
from fastapi.testclient import TestClient

from bnpl_cashflow.api.app import create_app
from tests.api.test_plans import setup


def test_rounding_shared_charge_completed_and_mixed_currency_roundtrip(setup, tmp_path):
    client, base, draft, _ = setup
    first = client.post(base + '/plans', json=draft).json()
    client.post(base + '/plans', json={**draft, 'plan_name': 'Second purchase'})
    client.post(base + '/plans', json={**draft, 'plan_name': 'US purchase', 'currency': 'USD'})
    client.post(base + '/plans', json={**draft, 'plan_name': 'Finished', 'paid_installment_count': '4'})
    response = client.get(base + '/plans/overview')
    assert response.status_code == 200, response.text
    overview = response.json()
    assert overview['summary'] == {
        'active_plans': 3,
        'remaining_totals': [{'currency': 'CAD', 'amount': '150.02'}, {'currency': 'USD', 'amount': '75.01'}],
        'next_charge': {'date': '2026-09-16', 'amounts': [{'currency': 'CAD', 'amount': '50.00'}, {'currency': 'USD', 'amount': '25.00'}]},
    }
    row = overview['plans'][0]
    assert row['id'] == first['id']
    assert row['credit_card_name'] == 'TD Visa'
    assert row['remaining_amount'] == '75.01'
    assert row['remaining_installment_count'] == 3
    assert row['progress_percent'] == 25
    completed = overview['plans'][-1]
    assert completed['completed'] is True
    assert completed['remaining_amount'] == '0.00'
    assert completed['remaining_installment_count'] == 0
    assert completed['progress_percent'] == 100
    exported = client.get(base + '/export')
    assert 'attachment' in exported.headers['content-disposition']
    assert not any('remaining_amount' in plan for plan in exported.json()['bnpl_plans'])
    other = TestClient(create_app(tmp_path / 'roundtrip.sqlite3'))
    assert other.post('/api/profiles/import', json=exported.json()).status_code == 201
    assert other.get(base + '/plans/overview').json() == overview
    assert other.get(base + '/export').json() == exported.json()


def test_edit_delete_refresh_identity_and_profile_isolation(setup):
    client, base, draft, _ = setup
    plan = client.post(base + '/plans', json=draft).json()
    other = client.post('/api/profiles', json={'name': 'Other'}).json()
    other_base = f'/api/profiles/{other["id"]}'
    endpoint = base + '/plans/' + plan['id']
    for method in (client.patch, client.delete):
        kwargs = {'json': draft} if method == client.patch else {}
        assert method(other_base + '/plans/' + plan['id'], **kwargs).status_code == 404
    assert client.get(other_base + '/plans/overview').json() == {
        'plans': [], 'summary': {'active_plans': 0, 'remaining_totals': [], 'next_charge': None},
    }
    assert client.patch(endpoint, json={**draft, 'paid_installment_count': '5'}).status_code == 422
    assert client.get(base + '/plans').json() == [plan]
    updated = client.patch(endpoint, json={**draft, 'plan_name': 'Updated', 'paid_installment_count': '3'}).json()
    assert updated['id'] == plan['id']
    assert updated['credit_card_id'] == draft['credit_card_id']
    overview = client.get(base + '/plans/overview').json()
    assert overview['summary']['remaining_totals'] == [{'currency': 'CAD', 'amount': '25.01'}]
    assert overview['summary']['next_charge'] == {'date': '2026-10-14', 'amounts': [{'currency': 'CAD', 'amount': '25.01'}]}
    assert client.delete(endpoint).status_code == 200
    assert client.delete(endpoint).status_code == 404
    assert client.get(base + '/plans/overview').json()['summary']['next_charge'] is None
    assert client.get(base + '/export').json()['bnpl_plans'] == []
    assert client.get('/api/profiles').json()[1]['plan_count'] == 0


def test_exact_amount_paid_is_used_and_preserved_on_edit(setup):
    client, base, draft, _ = setup
    plan = client.post(base + '/plans', json={**draft, 'amount_paid': '25.02'}).json()
    before = client.get(base + '/plans/overview').json()
    assert before['plans'][0]['remaining_amount'] == '74.99'
    assert client.patch(base + '/plans/' + plan['id'], json={**draft, 'plan_name': 'Renamed'}).json()['amount_paid'] == '25.02'
    assert client.get(base + '/plans/overview').json()['plans'][0]['remaining_amount'] == '74.99'


@pytest.mark.parametrize('field', ['id', 'profile_id'])
def test_edit_rejects_identity_overrides(setup, field):
    client, base, draft, _ = setup
    plan = client.post(base + '/plans', json=draft).json()
    assert client.patch(base + '/plans/' + plan['id'], json={**draft, field: 'foreign'}).status_code == 422
    assert client.get(base + '/plans').json() == [plan]


def test_plan_appearance_persists_edits_exports_and_roundtrips(setup, tmp_path):
    client, base, draft, path = setup
    created = client.post(base + '/plans', json={**draft, 'icon': 'laptop', 'icon_color': 'purple'})
    assert created.status_code == 201, created.text
    plan = created.json()
    assert (plan['icon'], plan['icon_color']) == ('laptop', 'purple')
    endpoint = base + '/plans/' + plan['id']
    # Unrelated edits preserve presentation metadata and financial values.
    updated = client.patch(endpoint, json={**draft, 'plan_name': 'My laptop'}).json()
    assert (updated['icon'], updated['icon_color']) == ('laptop', 'purple')
    assert client.patch(endpoint, json={**draft, 'icon': 'star', 'icon_color': 'blue'}).status_code == 200
    report = TestClient(create_app(path)).get(base + '/plans/overview').json()
    assert report['plans'][0]['icon'] == 'star'
    assert report['plans'][0]['icon_color'] == 'blue'
    assert report['plans'][0]['remaining_amount'] == '75.01'
    exported = client.get(base + '/export').json()
    other = TestClient(create_app(tmp_path / 'icons.sqlite3'))
    assert other.post('/api/profiles/import', json=exported).status_code == 201
    assert other.get(base + '/export').json() == exported
    assert other.get(base + '/plans/overview').json() == report


@pytest.mark.parametrize('field,value', [('icon', 'unknown'), ('icon', '<svg>'), ('icon_color', 'red'), ('icon_color', ['purple'])])
def test_plan_appearance_rejects_invalid_values_without_writing(setup, field, value):
    client, base, draft, _ = setup
    assert client.post(base + '/plans', json={**draft, field: value}).status_code == 422
    assert client.get(base + '/plans').json() == []
    plan = client.post(base + '/plans', json=draft).json()
    assert client.patch(base + '/plans/' + plan['id'], json={**draft, field: value}).status_code == 422
    assert client.get(base + '/plans').json() == [plan]
    document = client.get(base + '/export').json()
    document['bnpl_plans'][0][field] = value
    document['profile']['id'] = 'invalid-import'
    document['profile']['name'] = 'Invalid import'
    for card in document['credit_cards']:
        card['profile_id'] = 'invalid-import'
    assert client.post('/api/profiles/import', json=document).status_code == 422
