import { useState } from 'react'
import { fireEvent, render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { expect, test } from 'vitest'
import { ProviderSelect } from './ProviderSelect'

function Example({ disabled = false }: { disabled?: boolean }) {
  const [value, setValue] = useState('')
  return <><label htmlFor="provider">Provider</label><ProviderSelect id="provider" value={value} disabled={disabled} invalid={false} describedBy="help" onChange={setValue} /><p id="help">Choose a provider</p><button>Outside</button></>
}

test('supports keyboard selection, Escape, typeahead, Tab, and a logo in the selected value', async () => {
  render(<Example />)
  const combo = screen.getByRole('combobox', { name: 'Provider' })
  combo.focus()
  await userEvent.keyboard('{ArrowDown}{End}{Enter}')
  expect(combo).toHaveTextContent('Affirm')
  expect(combo.querySelector('.provider-mark')).toHaveClass('provider-affirm')
  expect(combo.querySelector('img')).toHaveAttribute('src', '/providers/affirm.png')
  expect(combo).toHaveAttribute('aria-expanded', 'false')
  expect(combo).toHaveFocus()
  await userEvent.keyboard('{ArrowDown}{Home}{ArrowDown}{Escape}')
  expect(combo).toHaveTextContent('Affirm')
  await userEvent.keyboard('s{Enter}')
  expect(combo).toHaveTextContent('Sezzle')
  await userEvent.keyboard('{ArrowDown}{Tab}')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Outside' })).toHaveFocus()
})

test('shows each logo inside its option, closes on outside click, and respects disabled state', async () => {
  const view = render(<Example />)
  const combo = screen.getByRole('combobox', { name: 'Provider' })
  await userEvent.click(combo)
  for (const name of ['PayPal', 'Klarna', 'Afterpay', 'Sezzle', 'Affirm']) expect(screen.getByRole('option', { name }).querySelector('img')).toBeInTheDocument()
  fireEvent.pointerDown(screen.getByRole('button', { name: 'Outside' }))
  expect(combo).toHaveAttribute('aria-expanded', 'false')
  await userEvent.click(combo)
  await userEvent.click(screen.getByRole('option', { name: 'Klarna' }))
  expect(combo).toHaveTextContent('Klarna')
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
  view.rerender(<Example disabled />)
  expect(combo).toBeDisabled()
  await userEvent.click(combo)
  expect(screen.queryByRole('listbox')).not.toBeInTheDocument()
})
