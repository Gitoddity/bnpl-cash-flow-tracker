import { useEffect, useRef, useState } from 'react'
import { plansApi, type CurrencyAmount, type PaymentPlan, type PlanOverview } from './api'
import { Icon } from './Icon'
import { PlanIcon } from './PlanIcon'
import { ProviderBadge } from './ProviderBadge'

function money(currency: string, value: string) {
  // Formatting decimal text only; all amounts come from Python.
  const [whole, fraction = '00'] = value.split('.')
  return `${currency} ${whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}.${fraction.padEnd(2, '0')}`
}
function Amounts({ values }: { values: CurrencyAmount[] }) {
  return <>{values.map(item => <span className="plan-money" key={item.currency}>{money(item.currency, item.amount)}</span>)}</>
}
export function PaymentPlansOverview({ profileId, hasCards, onAdd, onAddCard, onEdit, onDeleted, onProjection, onBusyChange }: {
  profileId: string; hasCards: boolean; onAdd: () => void; onAddCard: () => void; onEdit: (plan: PaymentPlan) => void
  onDeleted: (plan: PaymentPlan) => void; onProjection: () => void; onBusyChange: (busy: boolean) => void
}) {
  const [data, setData] = useState<PlanOverview | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [deleting, setDeleting] = useState<PaymentPlan | null>(null)
  const [busy, setBusy] = useState(false)
  const [deleteError, setDeleteError] = useState('')
  const pending = useRef(false)
  const dialog = useRef<HTMLDialogElement>(null)
  const deleteTrigger = useRef<HTMLButtonElement | null>(null)
  useEffect(() => {
    let cancelled = false
    setData(null); setError('')
    plansApi.overview(profileId).then(value => { if (!cancelled) setData(value) })
      .catch(cause => { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Could not load payment plans.') })
    return () => { cancelled = true }
  }, [profileId, retry])
  useEffect(() => { if (deleting) dialog.current?.showModal() }, [deleting])
  function closeDelete() {
    if (pending.current) return
    dialog.current?.close(); setDeleting(null); setDeleteError(''); deleteTrigger.current?.focus()
  }
  async function confirmDelete() {
    if (!deleting || pending.current) return
    pending.current = true; setBusy(true); onBusyChange(true); setDeleteError('')
    try {
      await plansApi.delete(profileId, deleting.id)
      dialog.current?.close(); setDeleting(null); setData(null); setRetry(value => value + 1)
      onDeleted(deleting)
    } catch (cause) { setDeleteError(cause instanceof Error ? cause.message : 'Could not delete this plan.') }
    finally { pending.current = false; setBusy(false); onBusyChange(false) }
  }
  return <section className="plans-overview" aria-labelledby="plans-title">
    <div className="cards-overview-heading"><div className="card-page-heading"><h1 id="plans-title">Payment Plans</h1><p>Manage your purchases and remaining installment schedules.</p></div><button className="button primary" onClick={onAdd}><Icon name="plus" />Add Payment Plan</button></div>
    {error ? <div className="error-panel" role="alert"><p>{error}</p><button className="text-button" onClick={() => setRetry(value => value + 1)}>Retry</button></div>
    : !data ? <p className="plans-loading" role="status">Loading payment plans…</p>
    : <>
      <div className="plan-summaries">
        <section className="plan-summary"><h2>Active Plans</h2><strong className="plan-summary-value">{data.summary.active_plans}</strong></section>
        <section className="plan-summary"><h2>Remaining Installments Total</h2><div className="plan-summary-value">{data.summary.remaining_totals.length ? <Amounts values={data.summary.remaining_totals} /> : <span>No unpaid installments</span>}</div></section>
        <section className="plan-summary"><h2>Next Installment Charge</h2>{data.summary.next_charge ? <><div className="plan-summary-value"><Amounts values={data.summary.next_charge.amounts} /></div><time dateTime={data.summary.next_charge.date}>{new Date(`${data.summary.next_charge.date}T12:00:00`).toLocaleDateString('en-CA', { month: 'short', day: 'numeric', year: 'numeric' })}</time></> : <p>No upcoming charges</p>}<p className="charge-help">Provider charge to your card</p></section>
      </div>
      {!hasCards ? <div className="plan-section no-cards-guidance"><h2>Add a credit card first</h2><p>Connect your payment plans to a card saved in this profile.</p><button className="button primary" onClick={onAddCard}>Add Credit Card</button></div>
      : !data.plans.length ? <div className="plan-section plans-empty"><h2>Add your first payment plan</h2><p>Add a purchase to see its remaining installment schedule.</p><button className="button primary" onClick={onAdd}>Add Payment Plan</button></div>
      : <div className="plans-table-wrap"><table className="plans-table"><caption className="sr-only">Payment plans for the active profile</caption><thead><tr>{['Plan', 'Credit Card', 'Progress', 'Remaining', 'Actions'].map(label => <th scope="col" key={label}>{label}</th>)}</tr></thead><tbody>
        {data.plans.map(plan => <tr key={plan.id} aria-label={plan.plan_name}>
          <th scope="row" data-label="Plan"><div className="plan-identity"><PlanIcon icon={plan.icon} color={plan.icon_color} /><div><strong>{plan.plan_name}</strong><span className="plan-detail"><ProviderBadge provider={plan.provider_name} /></span><span className="plan-detail">{plan.installment_count} installments</span></div></div></th>
          <td data-label="Credit Card"><span className="plan-card"><Icon name="wallet" />{plan.credit_card_name}</span></td>
          <td data-label="Progress"><div className="plan-progress"><span>{plan.paid_installment_count} of {plan.installment_count} paid</span><span className="plan-detail">{plan.remaining_installment_count} remaining</span><progress value={plan.progress_percent} max={100} aria-label={`${plan.plan_name}: ${plan.paid_installment_count} of ${plan.installment_count} paid`} />{plan.completed && <span className="completed-label">Completed</span>}</div></td>
          <td data-label="Remaining" className="plan-remaining"><strong className="plan-money">{money(plan.currency, plan.remaining_amount)}</strong><span className="plan-detail plan-money">of {money(plan.currency, plan.purchase_amount)}</span></td>
          <td data-label="Actions"><div className="plan-actions"><button aria-label={`Edit ${plan.plan_name}`} onClick={() => onEdit(plan)} disabled={busy}>Edit</button><button aria-label={`Delete ${plan.plan_name}`} onClick={event => { deleteTrigger.current = event.currentTarget; setDeleting(plan) }} disabled={busy}>Delete</button></div></td>
        </tr>)}
      </tbody></table></div>}
      <aside className="cards-next-step plans-next-step"><div><h2>Ready to see your credit card dues?</h2><p>See how your installment plans affect upcoming credit card statements and due dates.</p></div><button className="button primary" onClick={onProjection}>View Cash Flow Projection</button></aside>
    </>}
    <dialog ref={dialog} aria-labelledby="delete-plan-title" aria-describedby="delete-plan-description" onCancel={event => { event.preventDefault(); closeDelete() }}>
      <h2 id="delete-plan-title">Delete payment plan?</h2><p id="delete-plan-description">Delete “{deleting?.plan_name}” from this profile? This cannot be undone.</p>
      {deleteError && <p role="alert">{deleteError}</p>}<div className="dialog-actions"><button className="button secondary" onClick={closeDelete} disabled={busy} autoFocus>Cancel</button><button className="button primary" onClick={() => void confirmDelete()} disabled={busy}>{busy ? 'Deleting…' : 'Delete Payment Plan'}</button></div>
    </dialog>
  </section>
}
