import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, cardsApi, type Card, type CardDraft } from './api'
import { Icon } from './Icon'

const initialDraft: CardDraft = { name: '', current_balance: '', statement_end_day: '', payment_due_day: '' }
const fields: { key: keyof CardDraft; label: string; placeholder: string; help: string; mode?: 'decimal' | 'numeric' }[] = [
  { key: 'name', label: 'Card Nickname', placeholder: 'e.g., TD Visa, RBC Mastercard', help: 'Used to identify this card and connect payment plans to it.' },
  { key: 'statement_end_day', label: 'Statement Closing Day', placeholder: 'Day of month, e.g., 18', help: 'Used to determine which statement receives each installment charge.', mode: 'numeric' },
  { key: 'payment_due_day', label: 'Payment Due Day', placeholder: 'Day of month, e.g., 12', help: 'Used to estimate when the resulting credit card due must be paid.', mode: 'numeric' },
  { key: 'current_balance', label: 'Current Balance', placeholder: '500.00', help: 'The amount already owed on this card. DueMap includes it when projecting your upcoming credit card dues.', mode: 'decimal' },
]

export function AddCardScreen({ profileId, existingCard, onSaved, onCancel, onBusyChange }: {
  profileId: string; existingCard?: Card; onSaved: (card: Card) => void; onCancel: () => void; onBusyChange: (busy: boolean) => void
}) {
  const [draft, setDraft] = useState<CardDraft>(() => existingCard ? {
    name: existingCard.name, current_balance: existingCard.current_balance,
    statement_end_day: String(existingCard.statement_end_day), payment_due_day: String(existingCard.payment_due_day),
  } : initialDraft)
  const [errors, setErrors] = useState<Partial<Record<keyof CardDraft, string>>>({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const pending = useRef(false)
  const form = useRef<HTMLFormElement>(null)
  useEffect(() => {
    const first = fields.find(field => errors[field.key])
    if (!saving && first) form.current?.querySelector<HTMLInputElement>(`#card-${first.key}`)?.focus()
  }, [errors, saving])
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending.current) return
    pending.current = true
    setSaving(true); onBusyChange(true); setErrors({}); setError('')
    try { onSaved(await (existingCard ? cardsApi.update(profileId, existingCard.id, draft) : cardsApi.create(profileId, draft))) }
    catch (cause) {
      const mapped: Partial<Record<keyof CardDraft, string>> = {}
      const remaining: string[] = []
      if (cause instanceof ApiError && cause.issues.length) {
        for (const issue of cause.issues) {
          const field = fields.find(item => issue.path === `credit_cards[0].${item.key}`)
          if (field) mapped[field.key] = issue.message
          else remaining.push(issue.message)
        }
      } else remaining.push(cause instanceof Error ? cause.message : 'Could not save this card. Please try again.')
      setErrors(mapped); setError(remaining.join(' '))
    } finally { pending.current = false; setSaving(false); onBusyChange(false) }
  }
  function field(key: keyof CardDraft) {
    const item = fields.find(item => item.key === key)!
    return <div className="card-field" key={key}>
      <label htmlFor={`card-${key}`}>{item.label}{key === 'name' && <span aria-hidden="true"> *</span>}</label>
      <div className={key === 'current_balance' ? 'currency-input' : undefined}>
        {key === 'current_balance' && <span aria-hidden="true">$</span>}
        <input id={`card-${key}`} name={key} type="text" inputMode={item.mode} autoComplete="off"
          aria-required={key === 'name' || undefined} placeholder={item.placeholder} value={draft[key]} disabled={saving}
          aria-invalid={!!errors[key]} aria-describedby={`card-${key}-help${errors[key] ? ` card-${key}-error` : ''}`}
          onChange={event => setDraft(current => ({ ...current, [key]: event.target.value }))} />
      </div>
      <p className="field-help" id={`card-${key}-help`}>{item.help}</p>
      {errors[key] && <p className="error" role="alert" id={`card-${key}-error`}>{errors[key]}</p>}
    </div>
  }
  return <section className="add-card-screen" aria-labelledby="add-card-title">
    <div className="card-page-heading"><h1 id="add-card-title">{existingCard ? 'Edit Credit Card' : 'Add a Credit Card'}</h1>
      <p>Add the card’s billing schedule so DueMap can place your Klarna, Afterpay, and Sezzle installments into the correct credit card dues.</p></div>
    <aside className="card-privacy"><Icon name="shield" /><div><h2>No card credentials required</h2>
      <p>DueMap does not need your card number, expiry date, CVV, PIN, or online banking login. It cannot access your account or charge your card.</p>
      <p>Only enter a card nickname, its current balance, and the billing dates shown on your statement.</p></div></aside>
    <form ref={form} className="card-form" onSubmit={submit} noValidate aria-busy={saving}>
      <fieldset><legend>Card details</legend>{field('name')}</fieldset>
      <fieldset><legend>Statement &amp; payment cycle</legend><div className="billing-fields">{field('statement_end_day')}{field('payment_due_day')}</div></fieldset>
      <fieldset><legend>Current balance</legend>{field('current_balance')}</fieldset>
      {error && <div className="error-panel" role="alert">{error}</div>}
      <div className="card-form-actions"><button type="button" className="button secondary" onClick={onCancel} disabled={saving}>Cancel</button>
        <button className="button primary" type="submit" disabled={saving}>{saving ? 'Saving…' : existingCard ? 'Save Changes' : 'Save Card'}<Icon name="arrow-right" /></button></div>
    </form>
  </section>
}
