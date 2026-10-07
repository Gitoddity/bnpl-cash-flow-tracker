import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { ProjectionScreen } from './ProjectionScreen'
import { cardsApi, plansApi, profilesApi, projectionApi, type Projection } from './api'

vi.mock('./api', async original => ({ ...await original<typeof import('./api')>(),
  projectionApi: { get: vi.fn() }, profilesApi: { list: vi.fn() }, cardsApi: { list: vi.fn() }, plansApi: { overview: vi.fn() },
}))
const data: Projection = {
  as_of_date: '2026-09-01', start_date: '2026-09-01', end_date: '2027-03-01', months: 6, card_count: 1, plan_count: 2,
  cards: [{ id: 'c', name: 'RBC Visa' }], currencies: ['CAD'],
  monthly: [{ period: '2026-09', charges: [], dues: [{ currency: 'CAD', amount: '450.00' }] }],
  dues: [{ card_id: 'c', card_name: 'RBC Visa', statement_start: '2026-08-08', statement_close: '2026-09-07', due_date: '2026-09-27', currency: 'CAD', amount: '450.00', balance_amount: '0.00', installment_count: 2, plan_count: 2, contributing_total: '450.00', installments: [
    { plan_id: 'p', plan_name: 'Normatec 3 Legs', provider_name: 'affirm', installment_number: 2, installment_count: 4, charge_date: '2026-08-20', amount: '300.00' },
    { plan_id: 'p2', plan_name: 'MacBook Pro', provider_name: 'paypal', installment_number: 6, installment_count: 12, charge_date: '2026-09-02', amount: '150.00' },
  ] }],
}
beforeEach(() => {
  vi.resetAllMocks()
  vi.mocked(projectionApi.get).mockResolvedValue(data)
  vi.mocked(profilesApi.list).mockResolvedValue([{ id: 'personal', name: 'Personal', card_count: 1, plan_count: 2 }, { id: 'other', name: 'Other', card_count: 0, plan_count: 0 }])
  vi.mocked(cardsApi.list).mockResolvedValue([])
  vi.mocked(plansApi.overview).mockResolvedValue({ plans: [], summary: { active_plans: 0, remaining_totals: [], next_charge: null } })
  window.history.replaceState(null, '', '/#/profiles/personal/projection')
})
function standalone() { return render(<ProjectionScreen profileId="personal" onAddCard={vi.fn()} onAddPlan={vi.fn()} />) }

test('renders month totals and expandable dues with prior-period charge and distinct close/due dates', async () => {
  standalone()
  expect(screen.getByRole('status')).toHaveTextContent('Calculating')
  expect(await screen.findByRole('heading', { name: 'September 2026' })).toBeInTheDocument()
  const details = document.querySelector('.projection-due')!
  expect(details).toHaveAttribute('open')
  expect(within(details as HTMLElement).getByText('2 payment plans')).toBeInTheDocument()
  expect(screen.getByText('Affirm · Installment 2 of 4')).toBeInTheDocument()
  expect(screen.getByText('August 20, 2026')).toBeInTheDocument()
  expect(screen.getByText('September 7, 2026')).toBeInTheDocument()
  expect(screen.getByText('Total contributing installments')).toBeInTheDocument()
  expect(screen.queryByText('Minimum Payment')).not.toBeInTheDocument()
  await userEvent.click(details.querySelector('summary')!)
  expect(details).not.toHaveAttribute('open')
  await userEvent.click(details.querySelector('summary')!)
  expect(details).toHaveAttribute('open')
})

test('retry replaces calculation errors; period, card, currency and refresh call backend', async () => {
  vi.mocked(projectionApi.get).mockRejectedValueOnce(new Error('Invalid short month date'))
  standalone()
  expect(await screen.findByRole('alert')).toHaveTextContent('Invalid short month date')
  await userEvent.click(screen.getByRole('button', { name: 'Retry projection' }))
  await screen.findByText('Normatec 3 Legs')
  await userEvent.click(screen.getByText('Projection options'))
  fireEvent.change(screen.getByLabelText('Start month'), { target: { value: '2027-01' } })
  await waitFor(() => expect(projectionApi.get).toHaveBeenLastCalledWith('personal', expect.objectContaining({ start: '2027-01-01' })))
  await userEvent.selectOptions(screen.getByLabelText('Period'), '12')
  await userEvent.selectOptions(screen.getByLabelText('Credit card'), 'c')
  await userEvent.selectOptions(screen.getByLabelText('Currency'), 'CAD')
  await waitFor(() => expect(projectionApi.get).toHaveBeenLastCalledWith('personal', { start: '2027-01-01', months: 12, card_id: 'c', currency: 'CAD' }))
  const calls = vi.mocked(projectionApi.get).mock.calls.length
  await userEvent.click(screen.getByRole('button', { name: 'Refresh projection' }))
  await waitFor(() => expect(projectionApi.get).toHaveBeenCalledTimes(calls + 1))
})

test('both navigation paths mount projection and returning to it fetches fresh results', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  render(<App />)
  await userEvent.click(await screen.findByRole('button', { name: 'View Cash Flow Projection' }))
  expect(await screen.findByText('Normatec 3 Legs')).toBeInTheDocument()
  expect(window.location.hash).toBe('#/profiles/personal/projection')
  await userEvent.click(screen.getByRole('button', { name: 'Payment Plans' }))
  await screen.findByRole('button', { name: 'View Cash Flow Projection' })
  vi.mocked(projectionApi.get).mockResolvedValue({ ...data, dues: [], plan_count: 0 })
  await userEvent.click(screen.getByRole('button', { name: 'Projection' }))
  await screen.findByText('No card dues in this period')
  expect(screen.queryByText('Normatec 3 Legs')).not.toBeInTheDocument()
  expect(projectionApi.get).toHaveBeenCalledTimes(2)
  expect(screen.getByRole('button', { name: 'Projection' })).toHaveAttribute('aria-current', 'page')
  expect(screen.getByRole('link', { name: 'Export Profile' })).toHaveAttribute('href', '/api/profiles/personal/export')
})

test('currency totals and entered balances stay distinct without invented statement labels', async () => {
  const balance = { ...data.dues[0], currency: 'UNSPECIFIED', amount: '79.01', balance_amount: '79.01', installments: [], installment_count: 0, plan_count: 0, contributing_total: '0.00' }
  vi.mocked(projectionApi.get).mockResolvedValue({ ...data, dues: [balance], monthly: [{ period: '2026-09', charges: [], dues: [{ currency: 'UNSPECIFIED', amount: '79.01' }, { currency: 'USD', amount: '12.34' }] }] })
  standalone()
  await screen.findByText('Entered card balance due')
  expect(screen.getByText('USD 12.34')).toBeInTheDocument()
  expect(screen.getAllByText('Currency unspecified 79.01')).toHaveLength(3)
  expect(screen.getByText(/Card balances have no saved currency/)).toBeInTheDocument()
})

test('charge schedule remains available when card dues fall outside the selected period', async () => {
  vi.mocked(projectionApi.get).mockResolvedValue({ ...data, dues: [], charges: [{ plan_id: 'p', plan_name: 'Purchase', provider_name: 'affirm', card_id: 'c', card_name: 'RBC Visa', installment_number: 1, charge_date: '2026-09-20', statement_close: '2026-10-07', due_date: '2026-10-27', currency: 'CAD', amount: '123.45' }] })
  standalone()
  await screen.findByText('No card dues in this period')
  await userEvent.click(screen.getByText('Provider charges in the selected period'))
  const table = screen.getByRole('region', { name: 'Provider charge schedule' })
  expect(within(table).getByText('September 20, 2026')).toBeInTheDocument()
  expect(within(table).getByText('October 7, 2026')).toBeInTheDocument()
  expect(within(table).getByText('October 27, 2026')).toBeInTheDocument()
  expect(within(table).getByText('CAD 123.45')).toBeInTheDocument()
})

test('profile switch immediately clears results and ignores late previous-profile response', async () => {
  let finish!: (value: Projection) => void
  vi.mocked(projectionApi.get).mockReturnValueOnce(new Promise(resolve => { finish = resolve })).mockResolvedValueOnce({ ...data, card_count: 0, plan_count: 0, dues: [], cards: [] })
  render(<App />)
  await screen.findByLabelText('Switch active profile')
  await userEvent.selectOptions(screen.getByLabelText('Switch active profile'), 'other')
  await screen.findByRole('button', { name: 'Add Credit Card' })
  await act(async () => finish(data))
  expect(screen.queryByText('RBC Visa')).not.toBeInTheDocument()
  expect(window.location.hash).toBe('#/profiles/other/projection')
  expect(projectionApi.get).toHaveBeenLastCalledWith('other', expect.anything())
  await userEvent.click(screen.getByRole('button', { name: 'Add Credit Card' }))
  expect(window.location.hash).toBe('#/profiles/other/cards/new')
})

test('no-plan and empty-period guidance offers a real add-plan route', async () => {
  vi.mocked(projectionApi.get).mockResolvedValue({ ...data, plan_count: 0, dues: [] })
  render(<App />)
  await screen.findByRole('heading', { name: 'No payment plans yet' })
  expect(screen.getByRole('heading', { name: 'No card dues in this period' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Add Payment Plan' }))
  expect(window.location.hash).toBe('#/profiles/personal/plans/new')
})
