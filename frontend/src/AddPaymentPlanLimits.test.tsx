import { fireEvent, render, screen, within } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'
import { plansApi, type Card, type PaymentPlan, type PlanDraft } from './api'

vi.mock('./api', async original => ({ ...await original<typeof import('./api')>(), plansApi: { create: vi.fn() } }))
const card = { id: 'c1', profile_id: 'personal', name: 'Everyday Visa' } as Card
const draft: PlanDraft = { plan_name: 'Laptop', provider_name: 'klarna', credit_card_id: 'c1', purchase_amount: '900.00', currency: 'CAD', purchase_date: '2026-11-06', first_installment_date: '2026-11-06', installment_count: '4', paid_installment_count: '1' }
const saved = { ...draft, id: 'p1', installment_count: 4, paid_installment_count: 1, installment_frequency: 'BIWEEKLY', amount_paid: '0.00' } as PaymentPlan
const callbacks = { onSaved: vi.fn(), onCancel: vi.fn(), onAddCard: vi.fn(), onBusyChange: vi.fn() }
beforeEach(() => { vi.clearAllMocks(); vi.mocked(plansApi.create).mockResolvedValue(saved) })

test('total installments offers only 1 through 4 and requires a selection before saving', async () => {
  render(<AddPaymentPlanScreen profileId="personal" cards={[card]} {...callbacks} />)
  const total = screen.getByRole('combobox', { name: /Total Installments/ })
  expect(within(total).getAllByRole('option').map(option => (option as HTMLOptionElement).value)).toEqual(['', '1', '2', '3', '4'])
  expect(total).toHaveValue('')
  await userEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(screen.getByText('Choose between 1 and 4 installments.')).toBeInTheDocument()
  expect(total).toHaveFocus()
  expect(plansApi.create).not.toHaveBeenCalled()
})

test.each(['5', '-1', '1.5', ''])('rejects invalid paid installments %j without submitting', async value => {
  render(<AddPaymentPlanScreen profileId="personal" cards={[card]} initialValues={draft} {...callbacks} />)
  const paid = screen.getByRole('spinbutton', { name: /Paid Installments/ })
  fireEvent.change(paid, { target: { value } })
  expect(paid).toHaveAttribute('aria-invalid', 'true')
  expect(paid).toHaveAttribute('max', '4')
  await userEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(plansApi.create).not.toHaveBeenCalled()
  expect(paid).toHaveFocus()
  expect(screen.getByLabelText(/Purchase Amount/)).toHaveValue('900.00')
})

test('lowering the total flags excessive paid installments and correcting either field clears the error', async () => {
  render(<AddPaymentPlanScreen profileId="personal" cards={[card]} initialValues={draft} {...callbacks} />)
  const total = screen.getByRole('combobox', { name: /Total Installments/ })
  const paid = screen.getByRole('spinbutton', { name: /Paid Installments/ })
  fireEvent.change(paid, { target: { value: '4' } })
  await userEvent.selectOptions(total, '3')
  expect(screen.getByText('Paid installments cannot exceed total installments (3).')).toBeInTheDocument()
  expect(total).toHaveFocus()
  expect(paid).toHaveAttribute('max', '3')
  await userEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(plansApi.create).not.toHaveBeenCalled()
  await userEvent.selectOptions(total, '4')
  expect(paid).toHaveAttribute('aria-invalid', 'false')
  await userEvent.selectOptions(total, '3')
  fireEvent.change(paid, { target: { value: '3' } })
  expect(paid).toHaveAttribute('aria-invalid', 'false')
  expect(screen.queryByText(/Paid installments cannot exceed/)).not.toBeInTheDocument()
  await userEvent.click(screen.getByRole('button', { name: 'Save Payment Plan' }))
  expect(plansApi.create).toHaveBeenCalledWith('personal', expect.objectContaining({ installment_count: '3', paid_installment_count: '3' }))
})

test('editing also blocks excessive paid installments and accepts zero paid', async () => {
  const action = vi.fn().mockResolvedValue(saved)
  render(<AddPaymentPlanScreen profileId="personal" cards={[card]} initialValues={draft} submitAction={action} submitLabel="Save Changes" {...callbacks} />)
  const paid = screen.getByRole('spinbutton', { name: /Paid Installments/ })
  fireEvent.change(paid, { target: { value: '5' } })
  await userEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(action).not.toHaveBeenCalled()
  fireEvent.change(paid, { target: { value: '0' } })
  await userEvent.click(screen.getByRole('button', { name: 'Save Changes' }))
  expect(action).toHaveBeenCalledWith(expect.objectContaining({ installment_count: '4', paid_installment_count: '0' }))
})
