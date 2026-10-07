import { useEffect, useRef, useState, type FormEvent } from 'react'
import { ApiError, plansApi, providerNames, type Card, type PaymentPlan, type PlanDraft } from './api'
import { Icon } from './Icon'

const empty: PlanDraft = { plan_name: '', provider_name: '', credit_card_id: '', purchase_amount: '', currency: 'CAD', purchase_date: '', first_installment_date: '', installment_count: '', paid_installment_count: '0' }
const fields: { key: keyof PlanDraft; label: string; help: string; type?: string; placeholder?: string }[] = [
  { key: 'plan_name', label: 'Purchase / Plan Name', placeholder: 'e.g., Laptop, Flight, Furniture', help: 'Used to identify this purchase in your payment projection.' },
  { key: 'provider_name', label: 'Payment Plan Provider', help: '' },
  { key: 'credit_card_id', label: 'Credit Card', help: 'Select the credit card that receives the installment charges.' },
  { key: 'purchase_amount', label: 'Purchase Amount', help: 'The total amount financed through this payment plan.' },
  { key: 'currency', label: 'Currency', help: 'No currency conversion. All plans in a profile must use the same currency.' },
  { key: 'purchase_date', label: 'Purchase Date', type: 'date', help: 'The date the purchase was made.' },
  { key: 'first_installment_date', label: 'First Installment Date', type: 'date', help: 'The date the first installment was or will be charged.' },
  { key: 'installment_count', label: 'Total Installments', help: 'The total number of payments in the plan.' },
  { key: 'paid_installment_count', label: 'Paid Installments', help: 'Include installments already paid so DueMap projects only what remains.' },
]

export function AddPaymentPlanScreen({ profileId, cards, onCancel, onAddCard, onSaved, onBusyChange, initialValues, submitAction, submitLabel = 'Save Payment Plan', title = 'Add a Payment Plan' }: {
  profileId: string; cards: Card[]; onCancel: () => void; onAddCard: () => void; onSaved: (plan: PaymentPlan) => void
  onBusyChange: (busy: boolean) => void; initialValues?: PlanDraft; submitAction?: (draft: PlanDraft) => Promise<PaymentPlan>; submitLabel?: string; title?: string
}) {
  const [draft, setDraft] = useState<PlanDraft>(() => ({ ...empty, ...initialValues }))
  const [errors, setErrors] = useState<Partial<Record<keyof PlanDraft, string>>>({})
  const [error, setError] = useState('')
  const [saving, setSaving] = useState(false)
  const pending = useRef(false)
  const form = useRef<HTMLFormElement>(null)
  const activeCards = cards.filter(card => card.profile_id === profileId)
  useEffect(() => {
    if (!saving) form.current?.querySelector<HTMLElement>('[aria-invalid="true"], [data-form-error]')?.focus()
  }, [errors, error, saving])
  async function submit(event: FormEvent) {
    event.preventDefault()
    if (pending.current) return
    pending.current = true; setSaving(true); onBusyChange(true); setErrors({}); setError('')
    try { onSaved(await (submitAction ? submitAction(draft) : plansApi.create(profileId, draft))) }
    catch (cause) {
      const mapped: Partial<Record<keyof PlanDraft, string>> = {}
      const remaining: string[] = []
      if (cause instanceof ApiError && cause.issues.length) {
        for (const issue of cause.issues) {
          const field = fields.find(item => issue.path === `bnpl_plans[0].${item.key}` || issue.path === item.key)
          if (field) mapped[field.key] = issue.message
          else remaining.push(issue.message)
        }
      } else remaining.push(cause instanceof Error ? cause.message : 'Could not save this plan. Please try again.')
      setErrors(mapped); setError(remaining.join(' '))
    } finally { pending.current = false; setSaving(false); onBusyChange(false) }
  }
  function field(key: keyof PlanDraft) {
    const item = fields.find(item => item.key === key)!
    const props = { id: `plan-${key}`, name: key, value: draft[key], disabled: saving, required: true,
      'aria-invalid': !!errors[key], 'aria-describedby': `plan-${key}-help${errors[key] ? ` plan-${key}-error` : ''}`,
      onChange: (event: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => setDraft(current => ({ ...current, [key]: event.target.value })) }
    return <div className="card-field" key={key}><label htmlFor={props.id}>{item.label}<span aria-hidden="true"> *</span></label>
      {key === 'provider_name' ? <select {...props}><option value="" disabled>Select a provider</option>{Object.entries(providerNames).map(([value, label]) => <option key={value} value={value}>{label}</option>)}</select>
      : key === 'credit_card_id' ? <select {...props}><option value="" disabled>Select a credit card</option>{activeCards.map(card => <option key={card.id} value={card.id}>{card.name}</option>)}</select>
      : key === 'currency' ? <select {...props}><option>CAD</option><option>USD</option></select>
      : <input {...props} type={item.type || 'text'} inputMode={key === 'purchase_amount' ? 'decimal' : key.endsWith('_count') ? 'numeric' : undefined} placeholder={item.placeholder} autoComplete="off" />}
      <p className="field-help" id={`plan-${key}-help`}>{item.help}</p>
      {errors[key] && <p className="error" id={`plan-${key}-error`}>{errors[key]}</p>}
    </div>
  }
  return <section className="payment-plan-screen" aria-labelledby="plan-title">
    <div className="card-page-heading"><h1 id="plan-title">{title}</h1><p>Enter your installment schedule. DueMap will connect each installment to the correct credit card statement and due date.</p></div>
    {!activeCards.length ? <div className="plan-section no-cards-guidance"><h2>Add a credit card first</h2><p>Each payment plan must be connected to the credit card receiving its installment charges.</p><button className="button primary" onClick={onAddCard}>Add Credit Card</button><button className="button secondary" onClick={onCancel}>Cancel</button></div> : <>
      <aside className="card-privacy"><Icon name="shield" /><div><h2>No account credentials required</h2><p>Do not enter your payment provider password, credit card number, CVV, PIN, or online banking login. DueMap cannot access your accounts or make payments.</p><p>DueMap only needs the purchase amount, installment schedule, and the card receiving the charges.</p></div></aside>
      <form ref={form} className="payment-plan-form" onSubmit={submit} noValidate aria-busy={saving}>
        <fieldset className="plan-section"><legend>1. Payment plan details</legend>{field('plan_name')}{field('provider_name')}</fieldset>
        <fieldset className="plan-section"><legend>2. Pay with</legend>{field('credit_card_id')}</fieldset>
        <fieldset className="plan-section"><legend>3. Amount and schedule</legend><div className="plan-fields">{fields.slice(3).map(item => field(item.key))}</div><p className="plan-frequency">Payment frequency: <strong>Every two weeks</strong></p></fieldset>
        <aside className="plan-explanation"><h2>How your plan becomes a projection</h2><ul><li><strong>Amount and installment count:</strong> calculates each installment.</li><li><strong>First installment date:</strong> builds the installment schedule.</li><li><strong>Linked credit card:</strong> maps installments to the correct statement and due date.</li><li><strong>Paid installments:</strong> removes payments that have already occurred.</li></ul></aside>
        {error && <div className="error-panel" role="alert" tabIndex={-1} data-form-error>{error}</div>}
        <div className="card-form-actions"><button type="button" className="button secondary" onClick={onCancel} disabled={saving}>Cancel</button><button type="submit" className="button primary" disabled={saving}>{saving ? 'Saving?' : submitLabel}</button></div>
      </form>
    </>}
  </section>
}
