from datetime import date

from fastapi.testclient import TestClient
import pytest

from bnpl_cashflow.api.app import create_app


def setup_card(tmp_path, currency='CAD'):
    client = TestClient(create_app(tmp_path / 'currency.sqlite3', today_provider=lambda: date(2026, 11, 11)))
    profile = client.post('/api/profiles', json={'name': 'Sample'}).json()
    base = '/api/profiles/' + profile['id']
    draft = {'name': 'Tangerine', 'current_balance': '200',
             'upcoming_statement_close_date': '2026-11-17', 'upcoming_statement_due_date': '2026-12-14'}
    if currency is not None:
        draft['currency'] = currency
    response = client.post(base + '/cards', json=draft)
    return client, base, response


@pytest.mark.parametrize('currency', ['CAD', 'USD'])
def test_card_only_projection_uses_saved_currency_and_roundtrips(tmp_path, currency):
    client, base, response = setup_card(tmp_path, currency)
    assert response.status_code == 201, response.text
    assert response.json()['currency'] == currency
    view = client.get(base + '/projection').json()
    assert view['currencies'] == [currency]
    assert view['summary']['due_totals'] == [{'currency': currency, 'amount': '200.00'}]
    assert view['dues'][0]['currency'] == currency
    assert view['dues'][0]['due_date'] == '2026-12-14'
    assert client.get(base + '/projection?currency=' + currency).json()['dues'] == view['dues']
    exported = client.get(base + '/export').json()
    other = TestClient(create_app(tmp_path / 'roundtrip.sqlite3', today_provider=lambda: date(2026, 11, 11)))
    assert other.post('/api/profiles/import', json=exported).status_code == 201
    assert other.get(base + '/export').json() == exported
    assert other.get(base + '/projection').json() == view


def test_legacy_card_currency_can_be_set_without_changing_amount_or_dates(tmp_path):
    client, base, response = setup_card(tmp_path, None)
    card = response.json()
    assert 'currency' not in card
    assert client.get(base + '/projection').json()['dues'][0]['currency'] == 'UNSPECIFIED'
    changed = client.patch(base + '/cards/' + card['id'], json={'currency': 'cad'})
    assert changed.status_code == 200
    assert changed.json()['currency'] == 'CAD'
    assert changed.json()['current_balance'] == card['current_balance']
    assert changed.json()['upcoming_statement_due_date'] == card['upcoming_statement_due_date']
    assert client.get(base + '/projection').json()['dues'][0]['currency'] == 'CAD'
    # Invalid edits leave the saved currency unchanged.
    for invalid in ('', 'EUR', 123, ['CAD']):
        result = client.patch(base + '/cards/' + card['id'], json={'currency': invalid})
        assert result.status_code == 422
        assert result.json()['issues'][0]['path'] == 'credit_cards[0].currency'
    assert client.get(base + '/cards').json()[0]['currency'] == 'CAD'


def test_matching_plan_balance_combines_once_while_other_currencies_stay_separate(tmp_path):
    client, base, response = setup_card(tmp_path)
    card = response.json()
    draft = {'plan_name': 'Sample purchase', 'provider_name': 'klarna', 'credit_card_id': card['id'],
             'purchase_amount': '40', 'purchase_date': '2026-11-17', 'first_installment_date': '2026-11-17',
             'installment_count': 1, 'installment_frequency': 'BIWEEKLY'}
    for code in ('CAD', 'USD'):
        assert client.post(base + '/plans', json={**draft, 'currency': code}).status_code == 201
    view = client.get(base + '/projection').json()
    assert view['summary']['due_totals'] == [{'currency': 'CAD', 'amount': '240.00'}, {'currency': 'USD', 'amount': '40.00'}]
    assert len(view['dues']) == 2
    cad, usd = view['dues']
    assert (cad['currency'], cad['balance_amount'], cad['contributing_total']) == ('CAD', '200.00', '40.00')
    assert (usd['currency'], usd['balance_amount']) == ('USD', '0.00')
