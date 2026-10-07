import { useEffect, useState } from 'react'
import { cardsApi, plansApi, providerNames, type PaymentPlan, type Card, type ProfileSummary } from './api'
import { AddCardScreen } from './AddCardScreen'
import { ProfileEmptyState } from './ProfileEmptyState'
import { Icon } from './Icon'
import { displayDate } from './displayDate'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'

export function CardsWorkspace({ profile, page, saving, editingCard, onEdit, onUpdated, onAdd, onOverview, onPlan, onPlans, onPlanCancel, onPlanSaved, onProjection, onSaved, onBusyChange }: {
  profile: ProfileSummary; page: 'cards' | 'add-card' | 'edit-card' | 'plan' | 'plans' | 'projection'; saving: boolean
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
    if (page !== 'plans') return
    let cancelled = false
    setPlanError('')
    plansApi.list(profile.id).then(result => {
      // Keep a just-saved POST result visible even if a list response is stale.
      if (!cancelled) setPlans(current => [...result, ...(current || []).filter(plan => !result.some(item => item.id === plan.id))])
    })
      .catch(cause => { if (!cancelled) setPlanError(cause instanceof Error ? cause.message : 'Could not load plans.') })
    return () => { cancelled = true }
  }, [profile.id, page, retry])
  return <div className="cards-workspace">
    <aside className="workspace-sidebar" aria-label="Active workspace">
      <div className="workspace-profile"><span className="profile-avatar" aria-hidden="true">{profile.name.slice(0, 1).toUpperCase()}</span>
        <div><strong>{profile.name}</strong><span>Active workspace</span></div></div>
      <nav className="workspace-nav" aria-label="Profile navigation">
        <button onClick={onOverview} disabled={saving} aria-current={['cards', 'add-card', 'edit-card'].includes(page) ? 'page' : undefined}><Icon name="wallet" />Credit Cards</button>
        <button onClick={onPlans} disabled={saving} aria-current={['plan', 'plans'].includes(page) ? 'page' : undefined}><Icon name="calendar" />Payment Plans</button>
        <button onClick={onProjection} disabled={saving} aria-current={page === 'projection' ? 'page' : undefined}><Icon name="projection" />Projection</button>
      </nav>
      <p className="workspace-storage">Saved on this computer by the local server.</p>
    </aside>
    <div className="workspace-content">
      {error ? <section className="error-panel" role="alert"><p>{error}</p><button className="text-button" onClick={() => setRetry(value => value + 1)}>Retry loading cards</button></section>
      : cards === null ? <p role="status">Loading cards…</p>
      : page === 'edit-card' ? cardToEdit ? <AddCardScreen key={cardToEdit.id} profileId={profile.id} existingCard={cardToEdit} onCancel={onOverview} onBusyChange={onBusyChange} onSaved={card => {
        setCards(current => current!.map(item => item.id === card.id ? card : item)); onUpdated(card)
      }} /> : <section className="error-panel" role="alert"><p>This card is unavailable in this profile.</p><button className="button secondary" onClick={onOverview}>Back to Credit Cards</button></section>
      : page === 'add-card' ? <AddCardScreen key="new-card" profileId={profile.id} onCancel={onOverview} onBusyChange={onBusyChange} onSaved={card => {
        // The POST result is authoritative and appears immediately, without a second fetch.
        setCards(current => [...(current || []), card]); onSaved(card)
      }} />
      : page === 'plan' ? <AddPaymentPlanScreen profileId={profile.id} cards={cards} onCancel={onPlanCancel} onAddCard={onAdd} onBusyChange={onBusyChange} onSaved={plan => {
        setPlans(current => [...(current || []), plan]); onPlanSaved(plan)
      }} />
      : page === 'plans' ? <section className="plans-overview" aria-labelledby="plans-title">
        <div className="cards-overview-heading"><div className="card-page-heading"><h1 id="plans-title">Payment Plans</h1><p>Your purchases and remaining installment schedules.</p></div><button className="button primary" onClick={onPlan}><Icon name="plus" />Add Payment Plan</button></div>
        {planError && <div className="error-panel" role="alert">{planError}<button className="text-button" onClick={() => setRetry(value => value + 1)}>Retry loading plans</button></div>}
        {plans === null ? !planError && <p role="status">Loading payment plans?</p>
        : plans.length === 0 ? <div className="plan-section"><h2>No payment plans yet</h2><p>Add a purchase to see its installment schedule in DueMap.</p><button className="button primary" onClick={onPlan}>Add your first payment plan</button></div>
        : <div className="cards-grid">{plans.map(plan => <article className="saved-card" key={plan.id} aria-label={plan.plan_name}><h2>{plan.plan_name}</h2><p>{providerNames[plan.provider_name.toLowerCase() as keyof typeof providerNames] || plan.provider_name} ? {cards.find(card => card.id === plan.credit_card_id)?.name}</p><dl><div className="card-balance"><dt>Purchase amount</dt><dd>{plan.currency} {plan.purchase_amount}</dd></div><div><dt>Installments remaining</dt><dd>{plan.installment_count - plan.paid_installment_count} of {plan.installment_count}</dd></div><div><dt>First installment</dt><dd>{displayDate(plan.first_installment_date)}</dd></div></dl><p>Every two weeks</p></article>)}</div>}
      </section>
      : cards.length === 0 ? <div className="empty-cards"><ProfileEmptyState profile={profile} onAdd={onAdd} /></div>
      : page === 'projection' ? <section className="card-page-heading"><h1>Projection</h1><p>The projection screen is coming later. Your saved cards are ready.</p><button className="button secondary" onClick={onOverview}>Back to Credit Cards</button></section>
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
