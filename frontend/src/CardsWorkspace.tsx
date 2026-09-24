import { useEffect, useState } from 'react'
import { cardsApi, type Card, type ProfileSummary } from './api'
import { AddCardScreen } from './AddCardScreen'
import { ProfileEmptyState } from './ProfileEmptyState'
import { Icon } from './Icon'
import { displayDate } from './displayDate'
import { AddPaymentPlanScreen } from './AddPaymentPlanScreen'

export function CardsWorkspace({ profile, page, saving, editingCard, onEdit, onUpdated, onAdd, onOverview, onPlan, onProjection, onSaved, onBusyChange }: {
  profile: ProfileSummary; page: 'cards' | 'add-card' | 'edit-card' | 'plan' | 'projection'; saving: boolean
  editingCard?: string; onEdit: (card: Card) => void; onUpdated: (card: Card) => void
  onAdd: () => void; onOverview: () => void; onPlan: () => void; onProjection: () => void
  onSaved: (card: Card) => void; onBusyChange: (busy: boolean) => void
}) {
  const [cards, setCards] = useState<Card[] | null>(null)
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
  return <div className="cards-workspace">
    <aside className="workspace-sidebar" aria-label="Active workspace">
      <div className="workspace-profile"><span className="profile-avatar" aria-hidden="true">{profile.name.slice(0, 1).toUpperCase()}</span>
        <div><strong>{profile.name}</strong><span>Active workspace</span></div></div>
      <nav className="workspace-nav" aria-label="Profile navigation">
        <button onClick={onOverview} disabled={saving} aria-current={['cards', 'add-card', 'edit-card'].includes(page) ? 'page' : undefined}><Icon name="wallet" />Credit Cards</button>
        <button onClick={onPlan} disabled={saving} aria-current={page === 'plan' ? 'page' : undefined}><Icon name="calendar" />Payment Plans</button>
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
      : cards.length === 0 ? <div className="empty-cards"><ProfileEmptyState profile={profile} onAdd={onAdd} /></div>
      : page === 'plan' ? <AddPaymentPlanScreen cards={cards} onCancel={onOverview} onAddCard={onAdd} />
      : page === 'projection' ? <section className="card-page-heading"><h1>Projection</h1><p>The projection screen is coming later. Your saved cards are ready.</p><button className="button secondary" onClick={onOverview}>Back to Credit Cards</button></section>
      : <section className="cards-overview" aria-labelledby="cards-title">
        <div className="cards-overview-heading"><div className="card-page-heading"><h1 id="cards-title">Active Cards</h1><p>Manage your card statements and upcoming dues.</p></div>
          <button className="button primary" onClick={onAdd}><Icon name="plus" />Add Credit Card</button></div>
        <div className="cards-grid">{cards.map(card => <article className="saved-card" key={card.id} aria-label={card.name}>
          <div className="saved-card-heading"><span className="card-symbol"><Icon name="wallet" /></span><h2>{card.name}</h2>
            <button className="edit-card-button" aria-label={`Edit ${card.name}`} title="Edit credit card" onClick={() => onEdit(card)}><Icon name="pencil" /></button></div>
          <dl><div className="card-balance"><dt>Current balance</dt><dd>${card.current_balance}</dd></div>
            <div className="card-dates"><div><dt>Next statement closes:</dt><dd><time dateTime={card.next_statement_close_date}>{displayDate(card.next_statement_close_date)}</time></dd></div><div><dt>Next payment is due:</dt><dd><time dateTime={card.next_payment_due_date}>{displayDate(card.next_payment_due_date)}</time></dd></div></div></dl>
          <p className="card-as-of">As of <time dateTime={card.as_of_date}>{displayDate(card.as_of_date)}</time></p>
        </article>)}</div>
        <aside className="cards-next-step"><div><h2>Done adding your cards?</h2><p>Add your Klarna, Afterpay, and Sezzle plans and connect each plan to the card it will be charged to.</p></div>
          <button className="button primary" onClick={onPlan}><Icon name="plus" />Add Payment Plan</button></aside>
      </section>}
    </div>
  </div>
}
