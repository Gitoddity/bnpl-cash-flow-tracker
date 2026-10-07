from datetime import date

import pytest
from fastapi.testclient import TestClient

from bnpl_cashflow.api.app import create_app
from bnpl_cashflow.application.services import ApplicationService
from bnpl_cashflow.input.validation import validate_profile_payload
from tests.api.test_plans import setup


def test_projection_matches_pipeline_and_refreshes_after_changes(setup):
    client, base, draft, path = setup
    client = TestClient(create_app(path, today_provider=lambda: date(2026, 9, 1)))
    saved = client.post(base + '/plans', json={**draft, 'amount_paid': '25.02'}).json()
    view = client.get(base + '/projection?start=2026-09-01&months=3').json()
    document = client.get(base + '/export').json()
    result = ApplicationService(lambda: date(2026, 9, 1)).run(validate_profile_payload(document))
    assert [row['amount'] for row in view['charges']] == [format(item.installment_amount, '.2f') for item in result.installments]
    assert [row['statement_close'] for row in view['charges']] == [item.statement_cycle_end_date.isoformat() for item in result.projections]
    assert [row['due_date'] for row in view['charges']] == [item.cash_flow_due_date.isoformat() for item in result.projections]
    assert [row['amount'] for row in view['dues']] == [format(item.total_amount, '.2f') for item in result.cash_flow_obligations]
    assert view['summary']['due_totals'] == [{'currency': 'CAD', 'amount': '74.99'}]
    assert view['monthly'][0]['dues'] == []
    assert view['monthly'][1]['dues'] == [{'currency': 'CAD', 'amount': '25.00'}]
    assert view['monthly'][2]['dues'] == [{'currency': 'CAD', 'amount': '49.99'}]
    endpoint = base + '/plans/' + saved['id']
    assert client.patch(endpoint, json={**draft, 'paid_installment_count': '4', 'amount_paid': '100.01'}).status_code == 200
    assert client.get(base + '/projection?start=2026-09-01').json()['charges'] == []
    client.delete(endpoint)
    assert client.get(base + '/projection').json()['plan_count'] == 0
    card = document['credit_cards'][0]
    assert client.patch(base + '/cards/' + card['id'], json={
        'name': card['name'], 'current_balance': '123.45',
        'upcoming_statement_close_date': '2026-08-18',
        'upcoming_statement_due_date': '2026-09-12',
    }).status_code == 200
    view = client.get(base + '/projection').json()
    assert view['summary']['due_totals'] == [{'currency': 'UNSPECIFIED', 'amount': '123.45'}]


def test_mixed_currencies_balances_filters_and_profile_isolation(setup):
    client, base, draft, _ = setup
    client.post(base + '/plans', json=draft)
    client.post(base + '/plans', json={**draft, 'currency': 'USD'})
    card_id = draft['credit_card_id']
    client.patch(base + '/cards/' + card_id, json={
        'name': 'TD Visa', 'current_balance': '50.00',
        'upcoming_statement_close_date': '2026-09-18',
        'upcoming_statement_due_date': '2026-10-12',
    })
    query = '/projection?start=2026-09-01&months=6'
    view = client.get(base + query).json()
    assert view['summary']['due_totals'] == [
        {'currency': 'CAD', 'amount': '75.01'},
        {'currency': 'UNSPECIFIED', 'amount': '50.00'},
        {'currency': 'USD', 'amount': '75.01'},
    ]
    for currency, amount in [('CAD', '75.01'), ('USD', '75.01'), ('UNSPECIFIED', '50.00')]:
        filtered = client.get(base + query + '&currency=' + currency).json()
        assert filtered['summary']['due_totals'] == [{'currency': currency, 'amount': amount}]
    assert client.get(base + query + '&card_id=' + card_id).json()['dues'] == view['dues']
    other = client.post('/api/profiles', json={'name': 'Other'}).json()
    other_base = '/api/profiles/' + other['id']
    empty = client.get(other_base + query).json()
    assert empty['cards'] == empty['charges'] == empty['dues'] == []
    assert empty['card_count'] == empty['plan_count'] == 0
    assert client.get(other_base + query + '&card_id=' + card_id).status_code == 422
    assert client.get('/api/profiles/missing/projection').status_code == 404


@pytest.mark.parametrize('charge,close,due', [
    ('2026-02-28', '2026-02-28', '2026-03-05'),
    ('2026-03-01', '2026-03-28', '2026-04-05'),
    ('2028-02-29', '2028-03-28', '2028-04-05'),
    ('2026-12-28', '2026-12-28', '2027-01-05'),
])
def test_statement_boundary_short_month_and_next_month_due(tmp_path, charge, close, due):
    client = TestClient(create_app(tmp_path / 'dates.sqlite3', today_provider=lambda: date.fromisoformat(charge)))
    profile = client.post('/api/profiles', json={'name': 'Dates'}).json()
    base = '/api/profiles/' + profile['id']
    card = client.post(base + '/cards', json={'name': 'Month end', 'statement_end_day': 28, 'payment_due_day': 5}).json()
    response = client.post(base + '/plans', json={
        'plan_name': 'Purchase', 'provider_name': 'klarna', 'credit_card_id': card['id'],
        'purchase_amount': '12.34', 'currency': 'CAD', 'purchase_date': charge,
        'first_installment_date': charge, 'installment_count': '1',
        'installment_frequency': 'BIWEEKLY',
    })
    assert response.status_code == 201, response.text
    view = client.get(base + '/projection?start=' + charge + '&months=3').json()
    assert view['charges'][0]['statement_close'] == close
    assert view['charges'][0]['due_date'] == due
    assert view['monthly'][0]['dues'] == []
    assert next(row for row in view['monthly'] if row['period'] == due[:7])['dues'] == [{'currency': 'CAD', 'amount': '12.34'}]
    # A due in the following month is retained even when its charge is outside
    # the selected period. Charge and due windows are intentionally independent.
    later = client.get(base + '/projection?start=' + due + '&months=1').json()
    assert later['charges'] == []
    assert later['dues'][0]['due_date'] == due
    assert later['dues'][0]['plan_count'] == 1
    assert later['dues'][0]['contributing_total'] == '12.34'
    assert later['dues'][0]['installments'][0]['charge_date'] == charge
    assert later['dues'][0]['installments'][0]['installment_count'] == 1


@pytest.mark.parametrize('query', ['months=0', 'months=25', 'months=no', 'start=bad', 'start=9999-01-01', 'currency=EUR', 'card_id=missing'])
def test_invalid_projection_controls(setup, query):
    client, base, _, _ = setup
    assert client.get(base + '/projection?' + query).status_code == 422


def test_empty_selected_period(setup):
    client, base, draft, _ = setup
    client.post(base + '/plans', json=draft)
    view = client.get(base + '/projection?start=2030-01-01').json()
    assert view['charges'] == view['dues'] == view['summary']['due_totals'] == []
    assert view['summary']['next_due'] is None
    assert len(view['monthly']) == 6


def test_imported_short_month_calculation_error_remains_retryable(setup):
    client, base, draft, _ = setup
    client.post(base + '/plans', json=draft)
    document = client.get(base + '/export').json()
    document['profile'] = {'id': 'short-month', 'name': 'Short month'}
    card = document['credit_cards'][0]
    card['profile_id'] = 'short-month'
    card['statement_end_day'] = 31
    plan = document['bnpl_plans'][0]
    plan['purchase_date'] = plan['first_installment_date'] = '2026-02-01'
    assert client.post('/api/profiles/import', json=document).status_code == 201
    endpoint = '/api/profiles/short-month/projection?start=2026-02-01'
    response = client.get(endpoint)
    assert response.status_code == 422
    assert 'not valid' in response.json()['detail']
    assert client.get(endpoint).status_code == 422
    # Changing the input resolves the error on the next request, with no stale
    # result or stored error surviving the edit.
    assert client.patch('/api/profiles/short-month/cards/' + card['id'], json={
        'name': card['name'], 'current_balance': '0.00',
        'upcoming_statement_close_date': '2026-01-28',
        'upcoming_statement_due_date': '2026-02-12',
    }).status_code == 200
    assert client.get(endpoint).status_code == 200
