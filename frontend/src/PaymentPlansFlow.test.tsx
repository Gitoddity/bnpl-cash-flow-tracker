import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'
import { ApiError, cardsApi, plansApi, profilesApi, type Card, type PaymentPlan } from './api'
vi.mock('./api', async original => ({ ...await original<typeof import('./api')>(), profilesApi: { list: vi.fn() }, cardsApi: { list: vi.fn() }, plansApi: { list: vi.fn(), create: vi.fn() } }))
const profile = { id: 'personal', name: 'Personal', card_count: 1, plan_count: 0 }
const card = { id: 'c1', profile_id: 'personal', name: 'TD Visa' } as Card
const saved: PaymentPlan = { id: 'plan1', plan_name: 'Laptop', provider_name: 'affirm', credit_card_id: 'c1', purchase_amount: '100.01', currency: 'CAD', purchase_date: '2026-09-01', first_installment_date: '2026-09-02', installment_count: 4, paid_installment_count: 1, amount_paid: '0.00', installment_frequency: 'BIWEEKLY' }
beforeEach(() => {
  vi.resetAllMocks()
  window.history.replaceState(null, '', '/#/profiles/personal/plans/new')
  vi.mocked(profilesApi.list).mockResolvedValue([profile])
  vi.mocked(cardsApi.list).mockResolvedValue([card])
  vi.mocked(plansApi.list).mockResolvedValue([])
  vi.mocked(plansApi.create).mockResolvedValue(saved)
})
async function fill() {
  await screen.findByRole('heading', { name: 'Add a Payment Plan' })
  for (const [key, value] of Object.entries(saved)) {
    const input = document.querySelector(`[name="${key}"]`)
    if (input) fireEvent.change(input, { target: { value: String(value) } })
  }
}

test('five fixed providers start unselected, scoped cards and CAD default, no credential fields', async () => {
  render(<App />)
  const provider = await screen.findByLabelText(/Payment Plan Provider/)
  expect(provider).toHaveValue('')
  expect(provider.tagName).toBe('SELECT')
  expect(within(provider).getAllByRole('option').map(option => option.textContent)).toEqual(['Select a provider', 'PayPal', 'Klarna', 'Afterpay', 'Sezzle', 'Affirm'])
  expect(screen.getByLabelText(/Currency/)).toHaveValue('CAD')
  expect(screen.getByLabelText(/Paid Installments/)).toHaveValue('0')
  expect(screen.getByText('No account credentials required')).toBeInTheDocument()
  expect(document.querySelectorAll('input[type="password"]')).toHaveLength(0)
})

test('preserves all values and provider on field errors, focuses first invalid, and retains data after server failure', async () => {
  vi.mocked(plansApi.create).mockRejectedValueOnce(new ApiError('Invalid', [{ path: 'bnpl_plans[0].purchase_amount', message: 'must be positive' }, { path: 'bnpl_plans[0].plan_name', message: 'Check name' }])).mockRejectedValueOnce(new Error('Storage unavailable'))
  render(<App />); await fill()
  const before = Array.from(document.querySelectorAll('input, select')).map(input => (input as HTMLInputElement).value)
  fireEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(await screen.findByText('must be positive')).toBeInTheDocument()
  await waitFor(() => expect(screen.getByLabelText(/Purchase \/ Plan Name/)).toHaveFocus())
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveValue('affirm')
  expect(Array.from(document.querySelectorAll('input, select')).map(input => (input as HTMLInputElement).value)).toEqual(before)
  fireEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Storage unavailable')
  expect(screen.getByLabelText(/Purchase Amount/)).toHaveValue('100.01')
})

test('save uses active profile and stable values, blocks duplicates, immediately displays result, expires notice and refresh does not repeat it', async () => {
  let finish!: (plan: PaymentPlan) => void
  vi.mocked(plansApi.create).mockReturnValue(new Promise(resolve => { finish = resolve }))
  // A delayed list must not hide the authoritative POST result.
  vi.mocked(plansApi.list).mockReturnValue(new Promise(() => {}))
  const view = render(<App />); await fill()
  const button = screen.getByRole('button', { name: 'Save Payment Plan' })
  fireEvent.click(button); fireEvent.submit(button.closest('form')!)
  expect(plansApi.create).toHaveBeenCalledTimes(1)
  expect(plansApi.create).toHaveBeenCalledWith('personal', { plan_name: 'Laptop', provider_name: 'affirm', credit_card_id: 'c1', purchase_amount: '100.01', currency: 'CAD', purchase_date: '2026-09-01', first_installment_date: '2026-09-02', installment_count: '4', paid_installment_count: '1' })
  expect(screen.getByRole('button', { name: 'Cancel' })).toBeDisabled()
  expect(screen.getByRole('button', { name: 'Back' })).toBeDisabled()
  vi.useFakeTimers()
  try {
    await act(async () => { finish(saved) })
    expect(window.location.hash).toBe('#/profiles/personal/plans')
    expect(screen.getByRole('article', { name: 'Laptop' })).toHaveTextContent('3 of 4')
    expect(screen.getByRole('status')).toHaveTextContent('Laptop added successfully.')
    expect(screen.getByRole('button', { name: 'Add Another Plan' })).toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(4000) })
    expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
  } finally { vi.useRealTimers() }
  view.unmount(); vi.mocked(plansApi.list).mockResolvedValue([saved]); render(<App />)
  expect(await screen.findByRole('article', { name: 'Laptop' })).toBeInTheDocument()
  expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
})

test('overview and empty-state entry, cancel destination, add another and close notification', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  render(<App />)
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Add your first payment plan' }))
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(window.location.hash).toBe('#/profiles/personal/plans')
  await user.click(screen.getByRole('button', { name: 'Add Payment Plan' }))
  await fill(); vi.mocked(plansApi.list).mockResolvedValue([saved])
  await user.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  await user.click(await screen.findByRole('button', { name: 'Add Another Plan' }))
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveValue('')
  expect(screen.getByLabelText(/Purchase \/ Plan Name/)).toHaveValue('')
  await fill(); await user.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  await user.click(await screen.findByRole('button', { name: 'Dismiss success notification' }))
  expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
})

test('reusable form preselects saved fields and calls supplied edit action', async () => {
  const action = vi.fn().mockResolvedValue(saved)
  render(<AddPaymentPlanScreen profileId="personal" cards={[card, { ...card, id: 'foreign', profile_id: 'other', name: 'Other card' }]} initialValues={{ ...saved, installment_count: '4', paid_installment_count: '1' }} submitAction={action} submitLabel="Save Changes" onSaved={vi.fn()} onBusyChange={vi.fn()} onCancel={vi.fn()} onAddCard={vi.fn()} />)
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveValue('affirm')
  expect(screen.getByLabelText(/Credit Card/)).toHaveValue('c1')
  expect(screen.queryByRole('option', { name: 'Other card' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(action).toHaveBeenCalledOnce()
  expect(plansApi.create).not.toHaveBeenCalled()
})
