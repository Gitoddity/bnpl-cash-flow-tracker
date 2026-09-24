import { useState } from 'react'
import type { Card } from './api'
import { displayDate } from './displayDate'
import { Icon } from './Icon'

export function AddPaymentPlanScreen({ cards, onCancel, onAddCard }: {
  cards: Card[]; onCancel: () => void; onAddCard: () => void
}) {
  const [cardId, setCardId] = useState('')
  const selected = cards.find(card => card.id === cardId)
  return <section className="payment-plan-screen" aria-labelledby="plan-title">
    <div className="card-page-heading"><h1 id="plan-title">Add Payment Plan</h1><p>Log a new BNPL or installment purchase.</p></div>
    <form className="payment-plan-form" onSubmit={event => event.preventDefault()}>
      <fieldset className="plan-section"><legend>1. Payment plan details</legend>
        <label htmlFor="plan-name">Purchase / Plan Name</label>
        <input id="plan-name" placeholder="e.g., New laptop" autoComplete="off" />
        <label htmlFor="plan-provider">Payment Plan Provider</label>
        <select id="plan-provider" defaultValue=""><option value="" disabled>Select Provider</option>
          <option>Klarna</option><option>Afterpay</option><option>Sezzle</option><option>Other</option></select>
        <p className="plan-type-label">Plan Type</p><div className="plan-type">BNPL / Installments</div>
      </fieldset>
      <fieldset className="plan-section"><legend>2. Pay with</legend>
        <label htmlFor="plan-credit-card">Credit Card</label>
        <select id="plan-credit-card" value={cardId} onChange={event => setCardId(event.target.value)}>
          <option value="" disabled>Select a credit card</option>{cards.map(card => <option key={card.id} value={card.id}>{card.name}</option>)}
        </select>
        {selected && <div className="plan-card-summary"><div><Icon name="wallet" /><strong>{selected.name}</strong></div>
          <p>Next statement closes: <time dateTime={selected.next_statement_close_date}>{displayDate(selected.next_statement_close_date)}</time></p>
          <p>Next payment is due: <time dateTime={selected.next_payment_due_date}>{displayDate(selected.next_payment_due_date)}</time></p></div>}
        <button type="button" className="text-button" onClick={onAddCard}>Add Credit Card</button>
      </fieldset>
      <aside className="create-info" id="plan-saving-note"><Icon name="info" /><p>Plan saving is coming next. Details entered here are not saved yet.</p></aside>
      <div className="card-form-actions"><button type="button" className="button secondary" onClick={onCancel}>Cancel</button>
        <button type="submit" className="button primary" disabled aria-describedby="plan-saving-note">Add Payment Plan</button></div>
    </form>
  </section>
}
