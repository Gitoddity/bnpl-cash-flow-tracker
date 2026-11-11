import pytest
from fastapi.testclient import TestClient
from bnpl_cashflow.api.app import create_app
from bnpl_cashflow.application.services import run_application
from bnpl_cashflow.input.validation import validate_profile_payload

@pytest.fixture
def setup(tmp_path):
    path = tmp_path / 'plans.sqlite3'
    client = TestClient(create_app(path))
    profile = client.post('/api/profiles', json={'name': 'Personal'}).json()
    base = f'/api/profiles/{profile["id"]}'
    card = client.post(base + '/cards', json={'name': 'TD Visa', 'statement_end_day': 18, 'payment_due_day': 12}).json()
    draft = {'plan_name': 'Laptop', 'provider_name': 'paypal', 'credit_card_id': card['id'], 'purchase_amount': '100.01', 'currency': 'CAD', 'purchase_date': '2026-09-01', 'first_installment_date': '2026-09-02', 'installment_count': '4', 'paid_installment_count': '1', 'installment_frequency': 'BIWEEKLY'}
    return client, base, draft, path

@pytest.mark.parametrize('provider', ['paypal', 'klarna', 'afterpay', 'sezzle', 'affirm'])
def test_save_restart_export_import_and_calculations(setup, tmp_path, provider):
    client, base, draft, path = setup
    response = client.post(base + '/plans', json={**draft, 'provider_name': provider})
    assert response.status_code == 201, response.text
    plan = response.json()
    assert plan['provider_name'] == provider
    assert TestClient(create_app(path)).get(base + '/plans').json() == [plan]
    exported = client.get(base + '/export').json()
    other = TestClient(create_app(tmp_path / 'import.sqlite3'))
    assert other.post('/api/profiles/import', json=exported).status_code == 201
    assert other.get(base + '/export').json() == exported
    result = run_application(validate_profile_payload(exported))
    assert [i.installment_number for i in result.installments] == [2, 3, 4]
    assert [str(i.installment_amount) for i in result.installments] == ['25.00', '25.00', '25.01']
    assert [i.installment_date.isoformat() for i in result.installments] == ['2026-09-16', '2026-09-30', '2026-10-14']
    assert client.get('/api/profiles').json()[0]['plan_count'] == 1

@pytest.mark.parametrize('field,value', [
    ('plan_name', ''), ('provider_name', ''), ('provider_name', 'other'), ('credit_card_id', ''), ('credit_card_id', 'foreign'),
    ('purchase_amount', '0'), ('purchase_amount', '-1'), ('purchase_amount', 'oops'), ('purchase_amount', 'NaN'),
    ('purchase_date', ''), ('purchase_date', '2026-02-30'), ('first_installment_date', ''), ('first_installment_date', 'invalid'),
    ('installment_count', '0'), ('installment_count', '1.5'), ('installment_count', True),
    ('installment_count', '5'), ('installment_count', 5),
    ('paid_installment_count', '-1'), ('paid_installment_count', '1.5'), ('paid_installment_count', '5'),
])
def test_invalid_fields_do_not_save(setup, field, value):
    client, base, draft, _ = setup
    response = client.post(base + '/plans', json={**draft, field: value})
    assert response.status_code == 422, response.text
    assert any(field in issue['path'] for issue in response.json()['issues'])
    assert client.get(base + '/plans').json() == []

@pytest.mark.parametrize('field', ['plan_name', 'provider_name', 'credit_card_id', 'purchase_amount', 'purchase_date', 'first_installment_date', 'installment_count'])
def test_missing_fields(setup, field):
    client, base, draft, _ = setup
    del draft[field]
    response = client.post(base + '/plans', json=draft)
    assert response.status_code == 422
    assert any(issue['path'] == field for issue in response.json()['issues'])

def test_profile_isolation_and_currency_consistency(setup):
    client, base, draft, _ = setup
    other = client.post('/api/profiles', json={'name': 'Other'}).json()
    other_base = f'/api/profiles/{other["id"]}'
    assert client.post(other_base + '/plans', json=draft).status_code == 422
    assert client.get(other_base + '/plans').json() == []
    assert client.post(base + '/plans', json=draft).status_code == 201
    response = client.post(base + '/plans', json={**draft, 'currency': 'USD'})
    assert response.status_code == 201
    assert len(client.get(base + '/plans').json()) == 2

def test_paid_all_and_default_paid(setup):
    client, base, draft, _ = setup
    del draft['paid_installment_count']
    assert client.post(base + '/plans', json=draft).json()['paid_installment_count'] == 0
    assert client.post(base + '/plans', json={**draft, 'paid_installment_count': '4'}).status_code == 201
    result = run_application(validate_profile_payload(client.get(base + '/export').json()))
    assert len(result.plan_results[1].installments) == 0


@pytest.mark.parametrize('count', [1, 2, 3, 4])
def test_accepts_each_supported_total_with_all_installments_paid(setup, count):
    client, base, draft, _ = setup
    response = client.post(base + '/plans', json={**draft, 'installment_count': count, 'paid_installment_count': count})
    assert response.status_code == 201, response.text
    assert response.json()['installment_count'] == count
    assert response.json()['paid_installment_count'] == count


@pytest.mark.parametrize('changes,field', [
    ({'installment_count': '5'}, 'installment_count'),
    ({'installment_count': '3', 'paid_installment_count': '4'}, 'paid_installment_count'),
])
def test_invalid_installment_edit_preserves_the_saved_plan(setup, changes, field):
    client, base, draft, _ = setup
    saved = client.post(base + '/plans', json=draft).json()
    response = client.patch(base + '/plans/' + saved['id'], json={**draft, **changes})
    assert response.status_code == 422
    assert any(issue['path'] == f'bnpl_plans[0].{field}' for issue in response.json()['issues'])
    assert client.get(base + '/plans').json() == [saved]


@pytest.mark.parametrize('changes,field', [
    ({'installment_count': 5}, 'installment_count'),
    ({'installment_count': 3, 'paid_installment_count': 4}, 'paid_installment_count'),
])
def test_profile_import_cannot_bypass_installment_limits(setup, tmp_path, changes, field):
    client, base, draft, _ = setup
    assert client.post(base + '/plans', json=draft).status_code == 201
    document = client.get(base + '/export').json()
    document['bnpl_plans'][0].update(changes)
    other = TestClient(create_app(tmp_path / 'invalid-import.sqlite3'))
    response = other.post('/api/profiles/import', json=document)
    assert response.status_code == 422
    assert any(issue['path'] == f'bnpl_plans[0].{field}' for issue in response.json()['issues'])
    assert other.get('/api/profiles').json() == []


@pytest.mark.parametrize('balance', ['0.00', '100.00'])
def test_october_purchase_with_due_day_31_saves_and_projects(setup, balance):
    client, base, draft, _ = setup
    card_id = draft['credit_card_id']
    card = client.patch(base + '/cards/' + card_id, json={
        'name': 'Sample card', 'current_balance': balance,
        'upcoming_statement_close_date': '2026-10-28',
        'upcoming_statement_due_date': '2026-10-31',
    })
    assert card.status_code == 200
    response = client.post(base + '/plans', json={
        **draft, 'purchase_amount': '323', 'purchase_date': '2026-10-28',
        'first_installment_date': '2026-10-28', 'installment_count': 4,
        'paid_installment_count': 1,
    })
    assert response.status_code == 201, response.text
    assert client.get(base + '/plans/overview').json()['summary']['remaining_totals'] == [
        {'currency': 'CAD', 'amount': '242.25'},
    ]
    view = client.get(base + '/projection?start=2026-10-01&months=3').json()
    assert [(charge['charge_date'], charge['due_date'], charge['amount']) for charge in view['charges']] == [
        ('2026-11-11', '2026-11-30', '80.75'),
        ('2026-11-25', '2026-11-30', '80.75'),
        ('2026-12-09', '2026-12-31', '80.75'),
    ]
    assert [(due['due_date'], due['amount']) for due in view['dues'] if due['currency'] == 'CAD'] == [
        ('2026-11-30', '161.50'), ('2026-12-31', '80.75'),
    ]
    saved_card = client.get(base + '/export').json()['credit_cards'][0]
    assert saved_card['upcoming_statement_due_date'] == '2026-10-31'
