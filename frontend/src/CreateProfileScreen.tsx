import { useState, type FormEvent } from 'react'
import { profilesApi, type ProfileSummary } from './api'
import { Icon } from './Icon'
import { storageDescription } from './hosting'

export function CreateProfileScreen({ onCreated, onImport, importing, importError, onBusyChange }: {
  onCreated: (profile: ProfileSummary) => void
  onImport: () => void
  importing: boolean
  importError: string
  onBusyChange: (busy: boolean) => void
}) {
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [busy, setBusy] = useState(false)

  async function submit(event: FormEvent) {
    event.preventDefault()
    setBusy(true); onBusyChange(true); setError('')
    try { onCreated(await profilesApi.create(name)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Profile could not be created.') }
    finally { setBusy(false); onBusyChange(false) }
  }

  return <section className="create-profile-card" aria-labelledby="create-title">
    <div className="create-heading">
      <div className="create-mark"><Icon name="add-circle" /></div>
      <h1 id="create-title">New Profile</h1>
      <p>Create a profile to organize your credit cards and Klarna, Afterpay, and Sezzle plans.</p>
    </div>
    <form onSubmit={submit} noValidate>
      <label htmlFor="profile-name">Profile Name</label>
      <input id="profile-name" autoFocus value={name} onChange={event => setName(event.target.value)} placeholder="e.g., Personal, Household, Travel" disabled={busy || importing} aria-invalid={!!error} aria-describedby={error ? 'create-error' : undefined} />
      {error && <p id="create-error" className="error" role="alert">{error}</p>}
      <button className="button primary create-submit" disabled={busy || importing}>{busy ? 'Creating…' : 'Create Profile'}<Icon name="arrow-right" /></button>
    </form>
    <div className="or-divider"><span>OR</span></div>
    <div>
      <button className="button secondary create-import" onClick={onImport} disabled={busy || importing}><Icon name="upload" />{importing ? 'Importing…' : 'Import Profile'}</button>
      {importError && <p className="error" role="alert">{importError}</p>}
    </div>
    <aside className="create-info"><Icon name="info" /><p><strong>No sign-up required.</strong> {storageDescription}</p></aside>
  </section>
}
