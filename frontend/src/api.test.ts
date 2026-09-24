import { expect, test, vi } from 'vitest'
import { ApiError, cardsApi, profilesApi } from './api'

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
  const draft = { name: 'Card', current_balance: '-0.01', statement_end_day: '18', payment_due_day: '12' }
  await expect(cardsApi.create('profile one', draft)).rejects.toMatchObject({ issues, constructor: ApiError })
  expect(fetch).toHaveBeenLastCalledWith('/api/profiles/profile%20one/cards', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(draft),
  })
})
