import { useEffect, useRef, useState, type ChangeEvent } from 'react'
import { brand } from './brand'
import { profilesApi, type ProfileSummary } from './api'
import { CreateProfileScreen } from './CreateProfileScreen'
import { CardsWorkspace } from './CardsWorkspace'
import { Icon } from './Icon'

export default function App() {
  const upload = useRef<HTMLInputElement>(null)
  const [route, setRoute] = useState(window.location.hash || '#/')
  const [saving, setSaving] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [profiles, setProfiles] = useState<ProfileSummary[]>([])
  const [selected, setSelected] = useState<ProfileSummary | null>(null)
  const [loading, setLoading] = useState(true)
  const [createdNotice, setCreatedNotice] = useState<{ id: string; message: string; card?: boolean } | null>(null)

  async function loadProfiles() {
    setLoading(true); setError('')
    try { setProfiles(await profilesApi.list()) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Could not load profiles.') }
    finally { setLoading(false) }
  }
  useEffect(() => { document.title = `${brand.name} · Cash Flow Planner`; void loadProfiles() }, [])
  useEffect(() => {
    const onHashChange = () => {
      const destination = window.location.hash || '#/'
      setRoute(destination)
      setCreatedNotice(current => current && destination === `#/profiles/${encodeURIComponent(current.id)}` ? current : null)
    }
    window.addEventListener('hashchange', onHashChange)
    window.addEventListener('popstate', onHashChange)
    return () => {
      window.removeEventListener('hashchange', onHashChange)
      window.removeEventListener('popstate', onHashChange)
    }
  }, [])
  useEffect(() => {
    if (!createdNotice) return
    const timeout = window.setTimeout(() => setCreatedNotice(null), 4000)
    return () => window.clearTimeout(timeout)
  }, [createdNotice])
  useEffect(() => { window.scrollTo({ top: 0, left: 0, behavior: 'instant' }) }, [route])
  function navigate(destination: string) {
    setCreatedNotice(null)
    setError(''); setRoute(destination)
    // pushState avoids a queued hashchange racing the save notification.
    if (window.location.hash !== destination) window.history.pushState(null, '', destination)
  }
  const creating = route === '#/profiles/new'
  const editMatch = route.match(/^#\/profiles\/([^/]+)\/cards\/([^/]+)\/edit$/)
  const activeProfile = profiles.find(profile => ['', '/cards/new', '/plans/new', '/projection'].some(suffix => route === `#/profiles/${encodeURIComponent(profile.id)}${suffix}`) || editMatch?.[1] === encodeURIComponent(profile.id))
  const editingCard = editMatch?.[2]
  const addingCard = !!activeProfile && route.endsWith('/cards/new')
  const workspacePage = editingCard ? 'edit-card' : route.endsWith('/plans/new') ? 'plan' : route.endsWith('/projection') ? 'projection' : addingCard ? 'add-card' : 'cards'
  const overviewRoute = activeProfile ? `#/profiles/${encodeURIComponent(activeProfile.id)}` : '#/'
  const landing = route === '#/'
  function accepted(profile: ProfileSummary) {
    setProfiles(current => [...current.filter(item => item.id !== profile.id), profile])
    setSelected(profile); navigate(`#/profiles/${encodeURIComponent(profile.id)}`)
  }
  function created(profile: ProfileSummary) {
    accepted(profile)
    setCreatedNotice({ id: profile.id, message: `Profile ‘${profile.name}’ created successfully.` })
  }
  async function importFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    event.target.value = '' // Allow selecting the same file after a failed attempt.
    if (!file) return
    setBusy(true); setError('')
    try { accepted(await profilesApi.import(file)) }
    catch (cause) { setError(cause instanceof Error ? cause.message : 'Import failed.') }
    finally { setBusy(false) }
  }
  const importAction = () => upload.current?.click()

  return <>
    <header className="topbar"><div className={`topbar-inner${landing ? '' : ' transactional-header'}`}>
      {!landing && <button className="back-button" onClick={() => navigate(activeProfile && workspacePage !== 'cards' ? overviewRoute : '#/')} disabled={busy || saving}><Icon name="arrow-left" />Back</button>}
      <div className="identity"><span className="wordmark">{brand.name}</span><span className="tagline">{brand.tagline}</span></div>
      {!landing && <span className="header-balancer" aria-hidden="true" />}
    </div></header>
    {createdNotice && <div className="success-notification">
      <div className="success-message" role="status" aria-atomic="true"><Icon name="success" /><span>{createdNotice.message}</span></div>
      {createdNotice.card && <button className="button secondary" onClick={() => navigate(`${overviewRoute}/cards/new`)}>Add Another Card</button>}
      <button className="notification-close" aria-label="Dismiss success notification" onClick={() => setCreatedNotice(null)}><Icon name="close" /></button>
    </div>}
    <input ref={upload} type="file" accept=".json,application/json" aria-label="Import profile JSON file" hidden onChange={importFile} />
    <main className={creating ? 'create-profile-canvas' : activeProfile ? 'cards-canvas' : undefined}>
      {creating ? <CreateProfileScreen onCreated={created} onImport={importAction} importing={busy} importError={error} onBusyChange={setSaving} />
      : activeProfile ? <CardsWorkspace key={activeProfile.id} profile={activeProfile} page={workspacePage} saving={saving}
          editingCard={editingCard} onEdit={card => navigate(`${overviewRoute}/cards/${encodeURIComponent(card.id)}/edit`)}
          onUpdated={card => {
            navigate(overviewRoute)
            setCreatedNotice({ id: activeProfile.id, message: `${card.name} updated successfully.` })
          }}
          onAdd={() => navigate(`${overviewRoute}/cards/new`)} onOverview={() => navigate(overviewRoute)} onBusyChange={setSaving}
          onPlan={() => navigate(`${overviewRoute}/plans/new`)} onProjection={() => navigate(`${overviewRoute}/projection`)}
          onSaved={card => {
            setProfiles(current => current.map(profile => profile.id === activeProfile.id ? { ...profile, card_count: profile.card_count + 1 } : profile))
            setSelected(current => current?.id === activeProfile.id ? { ...current, card_count: current.card_count + 1 } : current)
            navigate(overviewRoute)
            setCreatedNotice({ id: activeProfile.id, message: `${card.name} added successfully.`, card: true })
          }} />
      : !landing ? <section className="landing"><h1>{loading ? 'Loading profile…' : 'Profile unavailable'}</h1><p>{loading ? 'Loading your saved profile.' : 'Return to the landing page to choose a saved profile.'}</p>{error && <p role="alert">{error}</p>}</section>
      : <section className="landing" aria-labelledby="landing-title">
        <div className="wallet-mark"><Icon name="wallet" /></div>
        <h1 id="landing-title">See your installments before they hit your credit card.</h1>
        <p className="intro">Track Klarna, Afterpay, and Sezzle plans in one place. See when installments are due and how they affect your upcoming credit card dues.</p>
        <div className="landing-actions">
          <button className="button primary" onClick={() => navigate('#/profiles/new')} disabled={busy || loading}><Icon name="plus" />Create New Profile</button>
          <button className="button secondary" onClick={importAction} disabled={busy || loading}><Icon name="upload" />{busy ? 'Importing…' : 'Import Profile'}</button>
        </div>
        <aside className="privacy"><Icon name="shield" /><div>
          <div className="privacy-heading">No Sign-Up Required <span className="badge">Local server</span></div>
          <p>Profiles are saved on this computer by the local server, not in your browser. Closing this tab won’t delete them. JSON export is coming later.</p>
        </div></aside>
        {error && <div className="error-panel" role="alert"><p>{error}</p><button className="text-button" onClick={() => void loadProfiles()} disabled={busy || loading}>Reload saved profiles</button></div>}
        {selected && <div className="profile-result" role="status"><strong>{selected.name} is ready.</strong><p>{selected.card_count} cards · {selected.plan_count} payment plans</p><p>Profile saved. Card and payment-plan editing will be available in the next step.</p></div>}
        {loading && <p role="status" className="small">Loading saved profiles…</p>}
        {profiles.length > 0 && <div className="saved-profiles"><label htmlFor="saved-profile">Saved profiles on this computer</label>
          <select id="saved-profile" value="" onChange={event => {
            const profile = profiles.find(item => item.id === event.target.value)
            if (profile) { setSelected(profile); navigate(`#/profiles/${encodeURIComponent(profile.id)}`) }
          }}>
            <option value="">Select a profile</option>{profiles.map(profile => <option key={profile.id} value={profile.id}>{profile.name}</option>)}
          </select></div>}
      </section>}
    </main>
  </>
}
