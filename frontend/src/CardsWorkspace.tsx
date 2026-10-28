import { useEffect, useState } from 'react'
import { cardsApi, plansApi, type PaymentPlan, type Card, type ProfileSummary } from './api'
import { AddCardScreen } from './AddCardScreen'
import { ProfileEmptyState } from './ProfileEmptyState'
import { Icon } from './Icon'
import { displayDate } from './displayDate'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'
import { PaymentPlansOverview } from './PaymentPlansOverview'
import { ProjectionScreen } from './ProjectionScreen'
import { demoMode } from './hosting'
import { ExportProfile } from './ExportProfile'

export function CardsWorkspace({ profile, profiles, onSwitchProfile, page, saving, editingPlan, onEditPlan, onPlanUpdated, onPlanDeleted, editingCard, onEdit, onUpdated, onAdd, onOverview, onPlan, onPlans, onPlanCancel, onPlanSaved, onProjection, onSaved, onBusyChange, onImport, onManageProfiles, onNewProfile }: {
  onImport: () => void; onManageProfiles: () => void; onNewProfile: () => void
  profiles: ProfileSummary[]; onSwitchProfile: (profileId: string) => void
  profile: ProfileSummary; page: 'cards' | 'add-card' | 'edit-card' | 'plan' | 'edit-plan' | 'plans' | 'projection'; saving: boolean
  editingPlan?: string; onEditPlan: (plan: PaymentPlan) => void; onPlanUpdated: (plan: PaymentPlan) => void; onPlanDeleted: (plan: PaymentPlan) => void
  onPlans: () => void; onPlanCancel: () => void; onPlanSaved: (plan: PaymentPlan) => void
  editingCard?: string; onEdit: (card: Card) => void; onUpdated: (card: Card) => void
  onAdd: () => void; onOverview: () => void; onPlan: () => void; onProjection: () => void
  onSaved: (card: Card) => void; onBusyChange: (busy: boolean) => void
}) {
  const [cards, setCards] = useState<Card[] | null>(null)
  const [plans, setPlans] = useState<PaymentPlan[] | null>(null)
  const [planError, setPlanError] = useState('')
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const cardToEdit = cards?.find(card => encodeURIComponent(card.id) === editingCard)
  useEffect(() => {
    let cancelled = false
    setError('')
    cardsApi.list(profile.id).then(result => { if (!cancelled) setCards(result) })
      .catch(cause => { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Could not load cards.') })
    return () => { cancelled = true }
  }, [profile.id, retry])
  useEffect(() => {
    if (page !== 'edit-plan') return
    let cancelled = false
    setPlanError(''); setPlans(null)
    plansApi.list(profile.id).then(result => {
      if (!cancelled) setPlans(result)
    })
      .catch(cause => { if (!cancelled) setPlanError(cause instanceof Error ? cause.message : 'Could not load plans.') })
    return () => { cancelled = true }
  }, [profile.id, page, retry])
  return <div className="cards-workspace">
    <aside className="workspace-sidebar" aria-label="Active workspace">
      <div className="workspace-profile"><span className="profile-avatar" aria-hidden="true">{profile.name.slice(0, 1).toUpperCase()}</span>
        <div><label className="sr-only" htmlFor="workspace-profile">Switch active profile</label><select id="workspace-profile" value={profile.id} onChange={event => onSwitchProfile(event.target.value)} disabled={saving}>{profiles.map(item => <option value={item.id} key={item.id}>{item.name}</option>)}</select><span>Active workspace</span></div></div>
      <nav className="workspace-nav" aria-label="Profile navigation">
        <button onClick={onOverview} disabled={saving} aria-current={['cards', 'add-card', 'edit-card'].includes(page) ? 'page' : undefined}><Icon name="wallet" />Credit Cards</button>
        <button onClick={onPlans} disabled={saving} aria-current={['plan', 'edit-plan', 'plans'].includes(page) ? 'page' : undefined}><Icon name="calendar" />Payment Plans</button>
        <button onClick={onProjection} disabled={saving} aria-current={page === 'projection' ? 'page' : undefined}><Icon name="projection" />Projection</button>
      </nav>
      {page === 'projection' && <nav className="workspace-profile-actions" aria-label="Profile actions">
        <ExportProfile profileId={profile.id} />
        <button onClick={onManageProfiles} disabled={saving}>Manage Profiles</button>
        <button onClick={onImport} disabled={saving}><Icon name="upload" />Import Profile</button>
        <button onClick={onNewProfile} disabled={saving}><Icon name="plus" />New Profile</button>
      </nav>}
      <p className="workspace-storage">{demoMode ? 'Temporary session. Download your profile to keep your changes.' : 'Saved on this computer by the local server.'}</p>
    </aside>
    <div className="workspace-content">
      {page === 'projection' ? <ProjectionScreen key={profile.id} profileId={profile.id} onAddCard={onAdd} onAddPlan={onPlan} />
      : error ? <section className="error-panel" role="alert"><p>{error}</p><button className="text-button" onClick={() => setRetry(value => value + 1)}>Retry loading cards</button></section>
      : cards === null ? <p role="status">Loading cards…</p>
      : page === 'edit-card' ? cardToEdit ? <AddCardScreen key={cardToEdit.id} profileId={profile.id} existingCard={cardToEdit} onCancel={onOverview} onBusyChange={onBusyChange} onSaved={card => {
        setCards(current => current!.map(item => item.id === card.id ? card : item)); onUpdated(card)
      }} /> : <section className="error-panel" role="alert"><p>This card is unavailable in this profile.</p><button className="button secondary" onClick={onOverview}>Back to Credit Cards</button></section>
      : page === 'add-card' ? <AddCardScreen key="new-card" profileId={profile.id} onCancel={onOverview} onBusyChange={onBusyChange} onSaved={card => {
        // The POST result is authoritative and appears immediately, without a second fetch.
        setCards(current => [...(current || []), card]); onSaved(card)
      }} />
      : page === 'edit-plan' ? planError ? <div className="error-panel" role="alert">{planError}<button className="text-button" onClick={() => setRetry(value => value + 1)}>Retry</button></div>
      : plans === null ? <p role="status">Loading payment plan…</p>
      : (() => {
        const plan = plans.find(item => encodeURIComponent(item.id) === editingPlan)
        return plan ? <AddPaymentPlanScreen key={plan.id} profileId={profile.id} cards={cards} title="Edit Payment Plan" submitLabel="Save Changes"
          initialValues={{ ...plan, installment_count: String(plan.installment_count), paid_installment_count: String(plan.paid_installment_count) }}
          submitAction={draft => plansApi.update(profile.id, plan.id, draft)} onSaved={onPlanUpdated} onCancel={onPlans} onAddCard={onAdd} onBusyChange={onBusyChange} />
          : <div className="error-panel" role="alert">This payment plan is unavailable in this profile.<button className="text-button" onClick={onPlans}>Back to Payment Plans</button></div>
      })()
      : page === 'plan' ? <AddPaymentPlanScreen key="new-plan" profileId={profile.id} cards={cards} onCancel={onPlanCancel} onAddCard={onAdd} onBusyChange={onBusyChange} onSaved={onPlanSaved} />
      : page === 'plans' ? <PaymentPlansOverview profileId={profile.id} hasCards={cards.length > 0} onAdd={onPlan} onAddCard={onAdd} onEdit={onEditPlan} onDeleted={onPlanDeleted} onProjection={onProjection} onBusyChange={onBusyChange} />
      : cards.length === 0 ? <div className="empty-cards"><ProfileEmptyState profile={profile} onAdd={onAdd} /></div>
      : <section className="cards-overview" aria-labelledby="cards-title">
        <div className="cards-overview-heading"><div className="card-page-heading"><h1 id="cards-title">Active Cards</h1><p>Manage your card statements and upcoming dues.</p></div>
          <button className="button primary" onClick={onAdd}><Icon name="plus" />Add Credit Card</button></div>
        <div className="cards-grid">{cards.map(card => <article className="saved-card" key={card.id} aria-label={card.name}>
          <div className="saved-card-heading"><span className="card-symbol"><Icon name="wallet" /></span><h2>{card.name}</h2>
            <button className="edit-card-button" aria-label={`Edit ${card.name}`} title="Edit credit card" onClick={() => onEdit(card)}><Icon name="pencil" /></button></div>
          <dl><div className="card-balance"><dt>Current balance</dt><dd>${card.current_balance.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}</dd></div>
            <div className="card-dates">
              <div><dt>Latest statement</dt>{card.upcoming_statement_close_date ? <>
                <dd>Closed <time dateTime={card.latest_statement_close_date}>{displayDate(card.latest_statement_close_date)}</time></dd>
                <dd className="card-payment card-payment-latest"><span>Payment due</span><time dateTime={card.latest_statement_due_date}>{displayDate(card.latest_statement_due_date)}</time></dd>
              </> : <dd className="statement-missing">Enter your latest statement dates using the edit button.</dd>}</div>
              <div><dt>Upcoming statement <span className="date-estimate">Estimated</span></dt>
                <dd>Closes <time dateTime={card.next_statement_close_date}>{displayDate(card.next_statement_close_date)}</time></dd>
                <dd className="card-payment card-payment-estimated"><span>Payment due</span><time dateTime={card.next_statement_due_date}>{displayDate(card.next_statement_due_date)}</time></dd>
              </div>
            </div></dl>
          <p className="card-as-of">As of <time dateTime={card.as_of_date}>{displayDate(card.as_of_date)}</time></p>
        </article>)}</div>
        <aside className="cards-next-step"><div><h2>Done adding your cards?</h2><p>Add your Klarna, Afterpay, and Sezzle plans and connect each plan to the card it will be charged to.</p></div>
          <button className="button primary" onClick={onPlan}><Icon name="plus" />Add Payment Plan</button></aside>
      </section>}
    </div>
  </div>
}
