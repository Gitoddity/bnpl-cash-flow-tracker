import { fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test, vi } from 'vitest'
import { AddCardScreen } from './AddCardScreen'
import { ApiError, cardsApi, type Card } from './api'

const saved = {
  id: 'card', profile_id: 'personal', name: 'Tvdya', current_balance: '500',
  statement_end_day: 15, payment_due_day: 30,
  upcoming_statement_close_date: '2026-10-15', upcoming_statement_due_date: '2026-10-30',
} as Card

test.each(['due', 'close'])('correcting the %s date clears the stale cross-field error and resubmits', async correction => {
  const create = vi.spyOn(cardsApi, 'create').mockRejectedValueOnce(new ApiError('Invalid dates', [
    { path: 'credit_cards[0].upcoming_statement_due_date', message: 'must be after the statement closing date' },
  ])).mockResolvedValueOnce(saved)
  const onSaved = vi.fn()
  render(<AddCardScreen profileId="personal" onSaved={onSaved} onCancel={vi.fn()} onBusyChange={vi.fn()} />)
  const user = userEvent.setup()
  await user.type(screen.getByLabelText(/Card Nickname/), 'Tvdya')
  await user.type(screen.getByLabelText('Current Balance'), '500')
  const close = screen.getByLabelText('Statement Closing Date')
  const due = screen.getByLabelText('Payment Due Date')
  fireEvent.change(close, { target: { value: correction === 'close' ? '2026-10-31' : '2026-10-15' } })
  fireEvent.change(due, { target: { value: correction === 'due' ? '2026-10-10' : '2026-10-30' } })
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('must be after the statement closing date')
  expect(due).toHaveAttribute('aria-invalid', 'true')
  fireEvent.change(correction === 'due' ? due : close, {
    target: { value: correction === 'due' ? '2026-10-30' : '2026-10-15' },
  })
  expect(screen.queryByRole('alert')).not.toBeInTheDocument()
  expect(due).toHaveAttribute('aria-invalid', 'false')
  expect(close).toHaveValue('2026-10-15')
  expect(due).toHaveValue('2026-10-30')
  await user.click(screen.getByRole('button', { name: 'Save Card' }))
  await waitFor(() => expect(onSaved).toHaveBeenCalledWith(saved))
  expect(create).toHaveBeenLastCalledWith('personal', {
    name: 'Tvdya', current_balance: '500',
    upcoming_statement_close_date: '2026-10-15', upcoming_statement_due_date: '2026-10-30',
  })
})
