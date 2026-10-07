import { expect, test, vi } from 'vitest'
import { ApiError, cardsApi, plansApi, profilesApi, projectionApi } from './api'

test('missing projection route explains an outdated API without hiding a missing profile', async () => {
  vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'Not Found' }), { status: 404 }))
    .mockResolvedValueOnce(new Response(JSON.stringify({ detail: 'This profile no longer exists.' }), { status: 404 }))
  await expect(projectionApi.get('p')).rejects.toThrow('Restart the DueMap API')
  await expect(projectionApi.get('missing')).rejects.toThrow('This profile no longer exists.')
})

test('import sends original file bytes to the validated API endpoint', async () => {
  const profile = { id: 'p', name: 'Personal', card_count: 0, plan_count: 0 }
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response(JSON.stringify(profile), { status: 201 }))
  const file = new File(['{}'], 'profile.json', { type: 'application/json' })
  expect(await profilesApi.import(file)).toEqual(profile)
  expect(fetch).toHaveBeenCalledWith('/api/profiles/import', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: file,
  })
})

test('backend field errors and network failures become readable errors', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({
    detail: 'Invalid', issues: [{ path: 'credit_cards[0].name', message: 'must not be empty' }],
  }), { status: 422 }))
  await expect(profilesApi.import(new File(['{}'], 'invalid.json'))).rejects.toThrow('credit_cards[0].name: must not be empty')
  fetch.mockRejectedValueOnce(new TypeError('Failed to fetch'))
  await expect(profilesApi.list()).rejects.toThrow('Cannot reach the local server')
})

test('card API preserves decimal text, scopes requests, and retains structured validation issues', async () => {
  const issues = [{ path: 'credit_cards[0].current_balance', message: 'must not be negative' }]
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValueOnce(new Response(JSON.stringify({ issues }), { status: 422 }))
  const draft = { name: 'Card', current_balance: '-0.01', upcoming_statement_close_date: '2026-10-18', upcoming_statement_due_date: '2026-11-12' }
  await expect(cardsApi.create('profile one', draft)).rejects.toMatchObject({ issues, constructor: ApiError })
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%20one/cards', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft),
  })
})


test('plan request uses stable provider/card IDs and sends unchanged decimal text with biweekly frequency', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}', { status: 201 }))
  const draft = { plan_name: 'Laptop', provider_name: 'paypal', credit_card_id: 'stable-card', purchase_amount: '100.01', currency: 'CAD', purchase_date: '2026-09-01', first_installment_date: '2026-09-02', installment_count: '4', paid_installment_count: '1' }
  await plansApi.create('profile one', draft)
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%20one/plans', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, installment_frequency: 'BIWEEKLY' }),
  })
})

test('overview, update, delete and export are scoped and encode profile and plan IDs', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch').mockResolvedValue(new Response('{}'))
  const draft = { plan_name: 'Laptop', provider_name: 'paypal', credit_card_id: 'c1', purchase_amount: '100.01', currency: 'CAD', purchase_date: '2026-09-01', first_installment_date: '2026-09-02', installment_count: '4', paid_installment_count: '1' }
  await plansApi.overview('profile/one')
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%2Fone/plans/overview', undefined)
  await plansApi.update('profile/one', 'plan/one', draft)
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%2Fone/plans/plan%2Fone', { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, installment_frequency: 'BIWEEKLY' }) })
  await plansApi.delete('profile/one', 'plan/one')
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%2Fone/plans/plan%2Fone', { method: 'DELETE' })
  expect(profilesApi.exportUrl('profile/one')).toBe('/api/profiles/profile%2Fone/export')
})
