import { act, fireEvent, render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { beforeEach, expect, test, vi } from 'vitest'
import App from './App'
import { cardsApi, profilesApi } from './api'

vi.mock('./api', async importOriginal => ({ ...await importOriginal<typeof import('./api')>(), profilesApi: { list: vi.fn(), create: vi.fn(), import: vi.fn() }, cardsApi: { list: vi.fn(), create: vi.fn() } }))
const personal = { id: 'p1', name: 'Personal', card_count: 0, plan_count: 0 }
beforeEach(() => {
  window.history.replaceState(null, '', '/')
  vi.clearAllMocks()
  vi.mocked(profilesApi.list).mockResolvedValue([])
  vi.mocked(cardsApi.list).mockResolvedValue([])
  vi.mocked(profilesApi.create).mockResolvedValue(personal)
  vi.mocked(profilesApi.import).mockResolvedValue(personal)
})

test('create action enters accessible profile flow and persists through API', async () => {
  const user = userEvent.setup()
  render(<App />)
  await user.click(screen.getByRole('button', { name: 'Create New Profile' }))
  expect(screen.getByRole('heading', { name: 'New Profile' })).toBeInTheDocument()
  expect(screen.getByPlaceholderText('e.g., Personal, Household, Travel')).toBeInTheDocument()
  await user.type(screen.getByLabelText('Profile Name'), 'Personal')
  await user.click(screen.getByRole('button', { name: 'Create Profile' }))
  expect(profilesApi.create).toHaveBeenCalledWith('Personal')
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(screen.getByText('Active profile')).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
  expect(window.location.hash).toBe('#/profiles/p1')
  expect(screen.queryByLabelText('Profile Name')).not.toBeInTheDocument()
  expect(screen.getByRole('status')).toHaveTextContent('Profile ‘Personal’ created successfully.')
  await user.click(screen.getByRole('button', { name: 'Dismiss success notification' }))
  expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
})

test('creation errors retain input beside field and Back returns to landing', async () => {
  const user = userEvent.setup()
  vi.mocked(profilesApi.create).mockRejectedValue(new Error('Profile already exists.'))
  render(<App />)
  await user.click(screen.getByRole('button', { name: 'Create New Profile' }))
  await user.type(screen.getByLabelText('Profile Name'), 'Personal')
  await user.click(screen.getByRole('button', { name: 'Create Profile' }))
  expect(await screen.findByRole('alert')).toHaveTextContent('Profile already exists.')
  expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
  expect(screen.getByLabelText('Profile Name')).toHaveValue('Personal')
  expect(screen.getByLabelText('Profile Name')).toHaveAttribute('aria-invalid', 'true')
  await user.click(screen.getByRole('button', { name: 'Back' }))
  expect(screen.queryByLabelText('Profile Name')).not.toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Create New Profile' })).toBeInTheDocument()
  expect(window.location.hash).toBe('#/')
})

test('landing import action opens the picker and uploads raw file to backend', async () => {
  const user = userEvent.setup()
  render(<App />)
  const input = screen.getByLabelText('Import profile JSON file') as HTMLInputElement
  const click = vi.spyOn(input, 'click')
  await user.click(screen.getByRole('button', { name: 'Import Profile' }))
  expect(click).toHaveBeenCalledTimes(1)
  const file = new File(['{"format":"bnpl-profile"}'], 'personal.json', { type: 'application/json' })
  await user.upload(input, file)
  expect(profilesApi.import).toHaveBeenCalledWith(file)
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
})

test('failed import displays server error and permits same-file retry', async () => {
  const user = userEvent.setup()
  vi.mocked(profilesApi.import).mockRejectedValueOnce(new Error('Unsupported version.'))
  render(<App />)
  const file = new File(['{}'], 'profile.json', { type: 'application/json' })
  const input = screen.getByLabelText('Import profile JSON file')
  await user.upload(input, file)
  expect(await screen.findByRole('alert')).toHaveTextContent('Unsupported version.')
  await user.upload(input, file)
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
})

test('saved profiles can be selected after reload', async () => {
  vi.mocked(profilesApi.list).mockResolvedValue([personal])
  render(<App />)
  await waitFor(() => expect(screen.getByRole('option', { name: 'Personal' })).toBeInTheDocument())
  fireEvent.change(screen.getByLabelText('Saved profiles on this computer'), { target: { value: 'p1' } })
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
})

test('empty names are submitted to backend rules and can be corrected', async () => {
  const user = userEvent.setup()
  vi.mocked(profilesApi.create).mockRejectedValueOnce(new Error('profile name must not be empty'))
  render(<App />)
  await user.click(screen.getByRole('button', { name: 'Create New Profile' }))
  await user.type(screen.getByLabelText('Profile Name'), '   ')
  await user.click(screen.getByRole('button', { name: 'Create Profile' }))
  expect(profilesApi.create).toHaveBeenCalledWith('   ')
  expect(await screen.findByRole('alert')).toHaveTextContent('profile name must not be empty')
  expect(screen.getByLabelText('Profile Name')).toHaveValue('   ')
  await user.clear(screen.getByLabelText('Profile Name'))
  await user.type(screen.getByLabelText('Profile Name'), 'Personal')
  await user.click(screen.getByRole('button', { name: 'Create Profile' }))
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
})

test('Create Profile screen reuses import and retains typed name on failure', async () => {
  const user = userEvent.setup()
  vi.mocked(profilesApi.import).mockRejectedValueOnce(new Error('Unsupported version.'))
  render(<App />)
  await user.click(screen.getByRole('button', { name: 'Create New Profile' }))
  await user.type(screen.getByLabelText('Profile Name'), 'Household')
  const input = screen.getByLabelText('Import profile JSON file') as HTMLInputElement
  const click = vi.spyOn(input, 'click')
  await user.click(screen.getByRole('button', { name: 'Import Profile' }))
  expect(click).toHaveBeenCalledOnce()
  const file = new File(['{}'], 'profile.json', { type: 'application/json' })
  await user.upload(input, file)
  expect(await screen.findByRole('alert')).toHaveTextContent('Unsupported version.')
  expect(screen.getByLabelText('Profile Name')).toHaveValue('Household')
  await user.upload(input, file)
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(profilesApi.create).not.toHaveBeenCalled()
})

test('profile URL restores active profile after refresh', async () => {
  window.history.replaceState(null, '', '/#/profiles/p1')
  vi.mocked(profilesApi.list).mockResolvedValue([personal])
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
  expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
})

test('creation notice disappears after four seconds and does not return on remount', async () => {
  const user = userEvent.setup()
  const view = render(<App />)
  await user.click(screen.getByRole('button', { name: 'Create New Profile' }))
  await user.type(screen.getByLabelText('Profile Name'), 'Personal')
  vi.useFakeTimers()
  try {
    await act(async () => { fireEvent.click(screen.getByRole('button', { name: 'Create Profile' })) })
    expect(screen.getByRole('status')).toHaveTextContent('Profile ‘Personal’ created successfully.')
    act(() => { vi.advanceTimersByTime(3999) })
    expect(screen.getByText(/created successfully/)).toBeInTheDocument()
    act(() => { vi.advanceTimersByTime(1) })
    expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
    expect(screen.getByRole('button', { name: 'Add Credit Card' })).toBeInTheDocument()
  } finally { vi.useRealTimers() }
  view.unmount()
  vi.mocked(profilesApi.list).mockResolvedValue([personal])
  render(<App />)
  expect(await screen.findByRole('heading', { name: 'Personal' })).toBeInTheDocument()
  expect(screen.queryByText(/created successfully/)).not.toBeInTheDocument()
})
