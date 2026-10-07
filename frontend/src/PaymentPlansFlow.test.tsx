import { act, fireEvent, render, screen, waitFor, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'
import { ApiError, cardsApi, plansApi, profilesApi, type Card, type PaymentPlan } from './api'
vi.mock('./api', async original => ({ ...await original<typeof import('./api')>(), profilesApi: { list: vi.fn() }, cardsApi: { list: vi.fn() }, plansApi: { list: vi.fn(), create: vi.fn(), overview: vi.fn(), update: vi.fn(), delete: vi.fn() } }))
const profile = { id: 'personal', name: 'Personal', card_count: 1, plan_count: 0 }
const card = { id: 'c1', profile_id: 'personal', name: 'TD Visa' } as Card
const saved: PaymentPlan = { id: 'plan1', plan_name: 'Laptop', provider_name: 'affirm', credit_card_id: 'c1', purchase_amount: '100.01', currency: 'CAD', purchase_date: '2026-09-01', first_installment_date: '2026-09-02', installment_count: 4, paid_installment_count: 1, amount_paid: '0.00', installment_frequency: 'BIWEEKLY' }
const overview = { plans: [{ ...saved, credit_card_name: 'TD Visa', remaining_installment_count: 3, completed: false, remaining_amount: '75.01', progress_percent: 25 }], summary: { active_plans: 1, remaining_totals: [{ currency: 'CAD', amount: '75.01' }], next_charge: { date: '2026-09-16', amounts: [{ currency: 'CAD', amount: '25.00' }] } } }
const emptyOverview = { plans: [], summary: { active_plans: 0, remaining_totals: [], next_charge: null } }
beforeEach(() => {
  vi.resetAllMocks()
  window.history.replaceState(null, '', '/#/profiles/personal/plans/new')
  vi.mocked(profilesApi.list).mockResolvedValue([profile])
  vi.mocked(cardsApi.list).mockResolvedValue([card])
  vi.mocked(plansApi.list).mockResolvedValue([saved])
  vi.mocked(plansApi.overview).mockResolvedValue(overview)
  vi.mocked(plansApi.create).mockResolvedValue(saved)
})
async function fill() {
  await screen.findByRole('heading', { name: 'Add a Payment Plan' })
  for (const [key, value] of Object.entries(saved)) {
    if (key === 'provider_name') continue
    const input = document.querySelector(`[name="${key}"]`)
    if (input) fireEvent.change(input, { target: { value: String(value) } })
  }
  await userEvent.click(screen.getByRole('combobox', { name: /Payment Plan Provider/ }))
  await userEvent.click(screen.getByRole('option', { name: 'Affirm' }))
}

test('five fixed providers start unselected, scoped cards and CAD default, no credential fields', async () => {
  render(<App />)
  const provider = await screen.findByLabelText(/Payment Plan Provider/)
  expect(provider).toHaveTextContent('Select a provider')
  expect(provider).toHaveAttribute('role', 'combobox')
  await userEvent.click(provider)
  const options = screen.getAllByRole('option')
  expect(options.filter(option => option.closest('[role="listbox"]')).map(option => option.textContent)).toEqual(['PayPal', 'Klarna', 'Afterpay', 'Sezzle', 'Affirm'])
  for (const option of within(screen.getByRole('listbox')).getAllByRole('option')) expect(option.querySelector('img')).toBeInTheDocument()
  await userEvent.keyboard('{Escape}')
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
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveTextContent('Affirm')
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
    expect(screen.getByRole('row', { name: 'Laptop' })).toHaveTextContent('3 remaining')
    expect(screen.getByRole('status')).toHaveTextContent('Laptop added successfully.')
    expect(screen.getByRole('button', { name: 'Add Another Plan' })).toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(4000) })
    expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
  } finally { vi.useRealTimers() }
  view.unmount(); vi.mocked(plansApi.list).mockResolvedValue([saved]); render(<App />)
  expect(await screen.findByRole('row', { name: 'Laptop' })).toBeInTheDocument()
  expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
})

test('overview and empty-state entry, cancel destination, add another and close notification', async () => {
  vi.mocked(plansApi.overview).mockResolvedValue(emptyOverview)
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  render(<App />)
  const user = userEvent.setup()
  await screen.findByRole('heading', { name: 'Add your first payment plan' })
  await user.click(screen.getAllByRole('button', { name: 'Add Payment Plan' })[0])
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(window.location.hash).toBe('#/profiles/personal/plans')
  await user.click(screen.getAllByRole('button', { name: 'Add Payment Plan' })[0])
  await fill(); vi.mocked(plansApi.list).mockResolvedValue([saved])
  await user.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  await user.click(await screen.findByRole('button', { name: 'Add Another Plan' }))
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveTextContent('Select a provider')
  expect(screen.getByLabelText(/Purchase \/ Plan Name/)).toHaveValue('')
  await fill(); await user.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  await user.click(await screen.findByRole('button', { name: 'Dismiss success notification' }))
  expect(screen.queryByText('Laptop added successfully.')).not.toBeInTheDocument()
})

test('reusable form preselects saved fields and calls supplied edit action', async () => {
  const action = vi.fn().mockResolvedValue(saved)
  render(<AddPaymentPlanScreen profileId="personal" cards={[card, { ...card, id: 'foreign', profile_id: 'other', name: 'Other card' }]} initialValues={{ ...saved, installment_count: '4', paid_installment_count: '1' }} submitAction={action} submitLabel="Save Changes" onSaved={vi.fn()} onBusyChange={vi.fn()} onCancel={vi.fn()} onAddCard={vi.fn()} />)
  expect(screen.getByLabelText(/Payment Plan Provider/)).toHaveTextContent('Affirm')
  expect(screen.getByLabelText(/Credit Card/)).toHaveValue('c1')
  expect(screen.queryByRole('option', { name: 'Other card' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(action).toHaveBeenCalledOnce()
  expect(plansApi.create).not.toHaveBeenCalled()
})

test('edit loads the saved plan, updates its identity, refreshes summaries, and shows a once-only notice', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(plansApi.update).mockResolvedValue({ ...saved, plan_name: 'Updated laptop' })
  render(<App />)
  await userEvent.click(await screen.findByRole('button', { name: 'Edit Laptop' }))
  expect(window.location.hash).toBe('#/profiles/personal/plans/plan1/edit')
  expect(await screen.findByLabelText(/Purchase \/ Plan Name/)).toHaveValue('Laptop')
  expect(screen.getByLabelText(/Paid Installments/)).toHaveValue('1')
  fireEvent.change(screen.getByLabelText(/Purchase \/ Plan Name/), { target: { value: 'Updated laptop' } })
  vi.mocked(plansApi.overview).mockResolvedValue({ ...overview, plans: [{ ...overview.plans[0], plan_name: 'Updated laptop' }] })
  await userEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(await screen.findByRole('row', { name: 'Updated laptop' })).toBeInTheDocument()
  expect(plansApi.update).toHaveBeenCalledWith('personal', 'plan1', expect.objectContaining({ plan_name: 'Updated laptop' }))
  expect(Object.keys(vi.mocked(plansApi.update).mock.calls[0][2]).sort()).toEqual(['plan_name', 'provider_name', 'credit_card_id', 'purchase_amount', 'currency', 'purchase_date', 'first_installment_date', 'installment_count', 'paid_installment_count'].sort())
  expect(screen.getByRole('status')).toHaveTextContent('Updated laptop updated successfully.')
  expect(plansApi.overview).toHaveBeenCalledTimes(2)
  await userEvent.click(screen.getByRole('button', { name: 'Dismiss success notification' }))
  expect(screen.queryByRole('status')).not.toBeInTheDocument()
})

test('delete names the plan, cancel saves nothing, failure can retry, success refreshes the overview', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(plansApi.delete).mockRejectedValueOnce(new Error('Storage unavailable')).mockResolvedValueOnce({ deleted: true })
  render(<App />)
  const user = userEvent.setup()
  await user.click(await screen.findByRole('button', { name: 'Delete Laptop' }))
  expect(screen.getByRole('dialog')).toHaveTextContent('Delete “Laptop”')
  await user.click(screen.getByRole('button', { name: 'Cancel' }))
  expect(plansApi.delete).not.toHaveBeenCalled()
  expect(screen.getByRole('button', { name: 'Delete Laptop' })).toHaveFocus()
  await user.click(screen.getByRole('button', { name: 'Delete Laptop' }))
  await user.click(screen.getByRole('button', { name: 'Delete Payment Plan' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Storage unavailable')
  vi.mocked(plansApi.overview).mockResolvedValue(emptyOverview)
  await user.click(screen.getByRole('button', { name: 'Delete Payment Plan' }))
  expect(await screen.findByRole('heading', { name: 'Add your first payment plan' })).toBeInTheDocument()
  expect(plansApi.delete).toHaveBeenLastCalledWith('personal', 'plan1')
  expect(screen.getByRole('status')).toHaveTextContent('Laptop deleted successfully.')
})

test('overview loading and retry never fabricate zero summaries; projection and export use active profile routes', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(plansApi.overview).mockRejectedValueOnce(new Error('Overview unavailable')).mockResolvedValueOnce(overview)
  render(<App />)
  expect(await screen.findByRole('alert')).toHaveTextContent('Overview unavailable')
  expect(screen.queryByRole('heading', { name: 'Active Plans' })).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Retry' }))
  expect(await screen.findByRole('row', { name: 'Laptop' })).toHaveTextContent('CAD 75.01')
  expect(screen.getByRole('link', { name: 'Export Profile' })).toHaveAttribute('href', '/api/profiles/personal/export')
  await userEvent.click(screen.getByRole('button', { name: 'View Cash Flow Projection' }))
  expect(window.location.hash).toBe('#/profiles/personal/projection')
})

test('switching profile discards a delayed overview and scopes cards, summaries and export', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(profilesApi.list).mockResolvedValue([profile, { ...profile, id: 'other', name: 'Other' }])
  let resolveFirst!: (value: typeof overview) => void
  vi.mocked(plansApi.overview).mockReturnValueOnce(new Promise(resolve => { resolveFirst = resolve })).mockResolvedValueOnce(emptyOverview)
  render(<App />)
  await screen.findByText('Loading payment plans…')
  await userEvent.selectOptions(screen.getByLabelText('Switch active profile'), 'other')
  await screen.findByRole('heading', { name: 'Add your first payment plan' })
  await act(async () => { resolveFirst(overview) })
  expect(screen.queryByRole('row', { name: 'Laptop' })).not.toBeInTheDocument()
  expect(plansApi.overview).toHaveBeenLastCalledWith('other')
  expect(cardsApi.list).toHaveBeenLastCalledWith('other')
  expect(screen.getByRole('link', { name: 'Export Profile' })).toHaveAttribute('href', '/api/profiles/other/export')
})

test('renders backend mixed-currency amounts and completed rows without recomputing financial values', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(plansApi.overview).mockResolvedValue({
    plans: [overview.plans[0], { ...overview.plans[0], id: 'finished', plan_name: 'Finished', paid_installment_count: 4, remaining_installment_count: 0, remaining_amount: '0.00', completed: true, progress_percent: 100 }],
    summary: { active_plans: 1, remaining_totals: [{ currency: 'CAD', amount: '75.01' }, { currency: 'USD', amount: '50.02' }], next_charge: { date: '2026-10-14', amounts: [{ currency: 'CAD', amount: '25.01' }, { currency: 'USD', amount: '12.51' }] } },
  })
  render(<App />)
  const row = await screen.findByRole('row', { name: 'Finished' })
  expect(row).toHaveTextContent('Completed')
  expect(row).toHaveTextContent('0 remaining')
  expect(row).toHaveTextContent('CAD 0.00')
  expect(within(row).getByRole('progressbar')).toHaveAttribute('value', '100')
  expect(screen.getByText('USD 50.02')).toBeInTheDocument()
  expect(screen.getByText('USD 12.51')).toBeInTheDocument()
  expect(screen.queryByText(/Affirm \?/)).not.toBeInTheDocument()
  expect(screen.getAllByRole('columnheader').map(cell => cell.textContent)).toEqual(['Plan', 'Credit Card', 'Progress', 'Remaining', 'Actions'])
})

test('overview without cards guides the user to add a credit card first', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(cardsApi.list).mockResolvedValue([])
  vi.mocked(plansApi.overview).mockResolvedValue(emptyOverview)
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Add a credit card first' })).toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Add Credit Card' }))
  expect(window.location.hash).toBe('#/profiles/personal/cards/new')
})

test('icon picker saves a purchase icon and color independently of the provider badge', async () => {
  render(<App />); await fill()
  await userEvent.click(screen.getByText('Plan icon'))
  await userEvent.click(screen.getByRole('button', { name: 'Laptop' }))
  await userEvent.click(screen.getByRole('button', { name: 'Purple icon color' }))
  expect(screen.getByRole('button', { name: 'Laptop' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByRole('button', { name: 'Purple icon color' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByRole('combobox', { name: /Payment Plan Provider/ }).querySelector('img')).toHaveAttribute('src', '/providers/affirm.png')
  await userEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(plansApi.create).toHaveBeenCalledWith('personal', expect.objectContaining({ icon: 'laptop', icon_color: 'purple', provider_name: 'affirm' }))
})

test('edit preselects the saved icon and color, and the overview shows the provider logo separately', async () => {
  window.history.replaceState(null, '', '/#/profiles/personal/plans')
  vi.mocked(plansApi.list).mockResolvedValue([{ ...saved, icon: 'plane', icon_color: 'green' }])
  vi.mocked(plansApi.overview).mockResolvedValue({ ...overview, plans: [{ ...overview.plans[0], icon: 'plane', icon_color: 'green' }] })
  render(<App />)
  const row = await screen.findByRole('row', { name: 'Laptop' })
  expect(row.querySelector('.plan-icon')).toHaveClass('plan-color-green')
  expect(row.querySelector('.provider-badge img')).toHaveAttribute('src', '/providers/affirm.png')
  await userEvent.click(screen.getByRole('button', { name: 'Edit Laptop' }))
  await screen.findByRole('heading', { name: 'Edit Payment Plan' })
  await userEvent.click(screen.getByText('Plan icon'))
  expect(screen.getByRole('button', { name: 'Travel' })).toHaveAttribute('aria-pressed', 'true')
  expect(screen.getByRole('button', { name: 'Green icon color' })).toHaveAttribute('aria-pressed', 'true')
})
