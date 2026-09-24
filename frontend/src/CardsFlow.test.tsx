import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { ApiError, cardsApi, profilesApi, type Card } from './api'

vi.mock('./api', async importOriginal => ({ ...await importOriginal<typeof import('./api')>(),
  profilesApi: { list: vi.fn(), create: vi.fn(), import: vi.fn() }, cardsApi: { list: vi.fn(), create: vi.fn(), update: vi.fn() },
}))
const profile = { id: 'personal', name: 'Personal', card_count: 0, plan_count: 0 }
const card: Card = { id: 'c1', profile_id: 'personal', name: 'TD Visa', current_balance: '500.00', statement_end_day: 18, payment_due_day: 12,
  as_of_date: '2026-09-24', next_statement_close_date: '2026-10-18', next_payment_due_date: '2026-10-12' }
beforeEach(() => {
  window.history.replaceState(null, '', '/#/profiles/personal')
  vi.resetAllMocks()
  vi.mocked(profilesApi.list).mockResolvedValue([profile])
  vi.mocked(cardsApi.list).mockResolvedValue([])
  vi.mocked(cardsApi.create).mockResolvedValue(card)
})
async function openForm() {
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Add Credit Card' }))
  expect(screen.getByRole('heading', { name: 'Add a Credit Card' })).toBeInTheDocument()
  return user
}
async function fillForm(user: ReturnType<typeof userEvent.setup>) {
  await user.type(screen.getByLabelText(/Card Nickname/), 'TD Visa')
  await user.type(screen.getByLabelText('Current Balance'), '500.00')
  await user.type(screen.getByLabelText('Statement Closing Day'), '18')
  await user.type(screen.getByLabelText('Payment Due Day'), '12')
}

test('opens a four-field credential-free form; cancel preserves the active profile without saving', async () => {
  render(<App />)
  const user = await openForm()
  expect(window.location.hash).toBe('#/profiles/personal/cards/new')
  expect(screen.getByText('No card credentials required')).toBeInTheDocument()
  expect(screen.getAllByRole('textbox')).toHaveLength(4)
  expect(screen.getAllByRole('textbox').map(input => input.getAttribute('name'))).toEqual(['name', 'statement_end_day', 'payment_due_day', 'current_balance'])
  await fillForm(user)
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(window.location.hash).toBe('#/profiles/personal')
  expect(screen.getByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(cardsApi.create).not.toHaveBeenCalled()
  await openForm()
  expect(screen.getByLabelText(/Card Nickname/)).toHaveValue('')
  await user.click(screen.getByRole('button', { name: 'Back' }))
  expect(window.location.hash).toBe('#/profiles/personal')
})

test('saves under the active profile, shows returned data and success, and adds another with fresh inputs', async () => {
  render(<App />)
  const user = await openForm()
  await fillForm(user)
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(cardsApi.create).toHaveBeenCalledWith('personal', { name: 'TD Visa', current_balance: '500.00', statement_end_day: '18', payment_due_day: '12' })
  const tile = await screen.findByRole('article', { name: 'TD Visa' })
  expect(within(tile).getByText('$500.00')).toBeInTheDocument()
  expect(within(tile).getByText('October 18, 2026')).toBeInTheDocument()
  expect(within(tile).getByText('October 12, 2026')).toBeInTheDocument()
  expect(screen.getByRole('heading', { name: 'Active Cards' })).toBeInTheDocument()
  expect(window.scrollTo).toHaveBeenLastCalledWith({ top: 0, left: 0, behavior: 'instant' })
  expect(screen.getByRole('status')).toHaveTextContent('TD Visa added successfully.')
  expect(window.location.hash).toBe('#/profiles/personal')
  await user.click(screen.getByRole('button', { name: 'Add Another Card' }))
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  for (const input of screen.getAllByRole('textbox')) expect(input).toHaveValue('')
  await fillForm(user)
  vi.mocked(cardsApi.create).mockResolvedValue({ ...card, id: 'c2', name: 'RBC Mastercard' })
  await user.clear(screen.getByLabelText(/Card Nickname/))
  await user.type(screen.getByLabelText(/Card Nickname/), 'RBC Mastercard')
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(await screen.findByRole('article', { name: 'RBC Mastercard' })).toBeInTheDocument()
  expect(screen.getByRole('article', { name: 'TD Visa' })).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Dismiss success notification' }))
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
})

test('maps backend field errors, retains all entered text, and surfaces unmapped failures', async () => {
  vi.mocked(cardsApi.create).mockRejectedValueOnce(new ApiError('Invalid', [
    { path: 'credit_cards[0].name', message: 'must not be empty' },
    { path: 'credit_cards[0].current_balance', message: 'must be a decimal string' },
    { path: 'credit_cards[0].statement_end_day', message: 'must be between 1 and 31' },
    { path: 'credit_cards[0].payment_due_day', message: 'must be between 1 and 31' },
    { path: '$', message: 'Please review this card.' },
  ])).mockRejectedValueOnce(new Error('Local storage unavailable.'))
  render(<App />)
  const user = await openForm()
  const values = ['   ', '32', '0', 'invalid']
  for (const [index, input] of screen.getAllByRole('textbox').entries()) await user.type(input, values[index])
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(await screen.findByText('Please review this card.')).toBeInTheDocument()
  for (const [index, input] of screen.getAllByRole('textbox').entries()) {
    expect(input).toHaveValue(values[index]); expect(input).toHaveAttribute('aria-invalid', 'true')
    expect(input).toHaveAccessibleDescription(/must/)
  }
  expect(screen.getByLabelText(/Card Nickname/)).toHaveFocus()
  expect(window.location.hash).toBe('#/profiles/personal/cards/new')
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Local storage unavailable.')
  expect(screen.getByLabelText('Current Balance')).toHaveValue('invalid')
})

test('pending saves prevent duplicate submits and navigation through form controls', async () => {
  let finish!: (card: Card) => void
  vi.mocked(cardsApi.create).mockReturnValue(new Promise(resolve => { finish = resolve }))
  render(<App />)
  const user = await openForm()
  await fillForm(user)
  const submit = screen.getByRole('button', { name: 'Save Card' })
  await user.dblClick(submit)
  fireEvent.submit(submit.closest('form')!)
  expect(cardsApi.create).toHaveBeenCalledTimes(1)
  expect(screen.getByRole('button', { name: 'Saving…' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled()
  await act(async () => { finish(card) })
  expect(screen.getByRole('article', { name: 'TD Visa' })).toBeInTheDocument()
})

test('notice expires after four seconds; refresh restores cards without showing success', async () => {
  const view = render(<App />)
  const user = await openForm()
  await fillForm(user)
  vi.useFakeTimers()
  try {
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Save Card' })) })
    expect(screen.getByRole('status')).toHaveTextContent('TD Visa added successfully.')
    act(() => { vi.advanceTimersByTime(3999) })
    expect(screen.getByRole('status')).toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(1) })
    expect(screen.queryByRole('status')).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
  } finally { vi.useRealTimers() }
  view.unmount()
  vi.mocked(profilesApi.list).mockResolvedValue([{ ...profile, card_count: 1 }])
  vi.mocked(cardsApi.list).mockResolvedValue([card])
  render(<App />)
  expect(await screen.findByRole('article', { name: 'TD Visa' })).toBeInTheDocument()
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
  expect(cardsApi.list).toHaveBeenLastCalledWith('personal')
})

test('opening another profile fetches only its cards; failed loads can be retried', async () => {
  const travel = { ...profile, id: 'travel', name: 'Travel' }
  vi.mocked(profilesApi.list).mockResolvedValue([profile, travel])
  vi.mocked(cardsApi.list).mockRejectedValueOnce(new Error('Server unavailable.')).mockResolvedValueOnce([card]).mockResolvedValueOnce([])
  render(<App />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Server unavailable.')
  await userEvent.click(screen.getByRole('button', { name: 'Retry loading cards' }))
  expect(await screen.findByRole('article', { name: 'TD Visa' })).toBeInTheDocument()
  act(() => { window.location.hash = '#/profiles/travel'; window.dispatchEvent(new HashChangeEvent('hashchange')) })
  expect(await screen.findByRole('heading', { name: 'Travel' })).toBeInTheDocument()
  expect(screen.queryByRole('article')).not.toBeInTheDocument()
  await waitFor(() => expect(cardsApi.list).toHaveBeenLastCalledWith('travel'))
})

test('payment-plan entry shows only active-profile cards, including a just-saved card', async () => {
  const user = userEvent.setup()
  vi.mocked(profilesApi.list).mockResolvedValue([profile, { ...profile, id: 'travel', name: 'Travel' }])
  render(<App />)
  await openForm()
  await fillForm(user)
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(await screen.findByText('Done adding your cards?')).toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Add Payment Plan' }))
  expect(screen.getByRole('heading', { name: 'Add Payment Plan' })).toBeInTheDocument()
  expect(window.location.hash).toBe('#/profiles/personal/plans/new')
  const selector = screen.getByLabelText('Credit Card')
  expect(within(selector).getAllByRole('option').map(option => option.textContent)).toEqual(['Select a credit card', 'TD Visa'])
  await user.selectOptions(selector, 'c1')
  expect(screen.getByText('October 12, 2026')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Payment Plan' })).toBeDisabled()
  expect(screen.queryByText(/added successfully/)).not.toBeInTheDocument()
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(screen.getByRole('heading', { name: 'Active Cards' })).toBeInTheDocument()
  const travelCard = { ...card, id: 'c2', profile_id: 'travel', name: 'Travel Card' }
  vi.mocked(cardsApi.list).mockResolvedValue([travelCard])
  act(() => { window.location.hash = '#/profiles/travel/plans/new'; window.dispatchEvent(new HashChangeEvent('hashchange')) })
  const travelSelector = await screen.findByLabelText('Credit Card')
  expect(within(travelSelector).getAllByRole('option').map(option => option.textContent)).toEqual(['Select a credit card', 'Travel Card'])
  expect(cardsApi.list).toHaveBeenLastCalledWith('travel')
})

test('empty profiles retain first-card action and have no payment-plan next-step panel', async () => {
  render(<App />)
  expect(await screen.findByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
  expect(screen.queryByText('Done adding your cards?')).not.toBeInTheDocument()
  expect(screen.queryByRole('button', { name: 'Add Payment Plan' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Payment Plans' }))
  expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
})

test('pencil prefills card, cancel discards changes, and successful edit replaces the card', async () => {
  vi.mocked(cardsApi.list).mockResolvedValue([card])
  const revised = { ...card, name: 'Corrected Card', current_balance: '125.50', next_payment_due_date: '2026-10-20', payment_due_day: 20 }
  vi.mocked(cardsApi.update).mockRejectedValueOnce(new ApiError('Invalid', [{ path: 'credit_cards[0].payment_due_day', message: 'must be between 1 and 31' }])).mockResolvedValue(revised)
  const user = userEvent.setup()
  const view = render(<App />)
  await user.click(await screen.findByRole('button', { name: 'Edit TD Visa' }))
  expect(screen.getByRole('heading', { name: 'Edit Credit Card' })).toBeInTheDocument()
  expect(screen.getByLabelText(/Card Nickname/)).toHaveValue('TD Visa')
  expect(screen.getByLabelText('Current Balance')).toHaveValue('500.00')
  expect(screen.getByLabelText('Statement Closing Day')).toHaveValue('18')
  expect(screen.getByLabelText('Payment Due Day')).toHaveValue('12')
  await user.clear(screen.getByLabelText(/Card Nickname/))
  await user.type(screen.getByLabelText(/Card Nickname/), 'Discard me')
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(cardsApi.update).not.toHaveBeenCalled()
  await user.click(screen.getByRole('button', { name: 'Edit TD Visa' }))
  expect(screen.getByLabelText(/Card Nickname/)).toHaveValue('TD Visa')
  await user.clear(screen.getByLabelText(/Card Nickname/))
  await user.type(screen.getByLabelText(/Card Nickname/), 'Corrected Card')
  await user.clear(screen.getByLabelText('Payment Due Day'))
  await user.type(screen.getByLabelText('Payment Due Day'), '32')
  await user.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('must be between 1 and 31')
  expect(screen.getByLabelText(/Card Nickname/)).toHaveValue('Corrected Card')
  await user.clear(screen.getByLabelText('Payment Due Day'))
  await user.type(screen.getByLabelText('Payment Due Day'), '20')
  await user.clear(screen.getByLabelText('Current Balance'))
  await user.type(screen.getByLabelText('Current Balance'), '125.50')
  await user.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(cardsApi.update).toHaveBeenLastCalledWith('personal', 'c1', { name: 'Corrected Card', current_balance: '125.50', statement_end_day: '18', payment_due_day: '20' })
  expect(await screen.findByRole('article', { name: 'Corrected Card' })).toHaveTextContent('October 20, 2026')
  expect(screen.getAllByRole('article')).toHaveLength(1)
  expect(screen.getByRole('status')).toHaveTextContent('Corrected Card updated successfully.')
  expect(cardsApi.create).not.toHaveBeenCalled()
  view.unmount()
  vi.mocked(cardsApi.list).mockResolvedValue([revised])
  render(<App />)
  expect(await screen.findByRole('article', { name: 'Corrected Card' })).toHaveTextContent('$125.50')
  expect(screen.queryByText(/updated successfully/)).not.toBeInTheDocument()
})
