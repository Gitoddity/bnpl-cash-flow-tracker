import { useEffect, useState } from 'react'
import { projectionApi, providerNames, type CurrencyAmount, type Projection, type ProjectionDue } from './api'
import { displayDate } from './displayDate'
import { Icon } from './Icon'

function money(currency: string, amount: string) {
  const [whole, fraction = '00'] = amount.split('.')
  return `${currency === 'UNSPECIFIED' ? 'Currency unspecified' : currency} ${whole.replace(/\B(?=(\d{3})+(?!\d))/g, ',')}.${fraction.padEnd(2, '0')}`
}
function Amounts({ values }: { values: CurrencyAmount[] }) {
  return <>{values.map(value => <span className="projection-money" key={value.currency}>{money(value.currency, value.amount)}</span>)}</>
}
function DueCard({ due, expanded }: { due: ProjectionDue; expanded: boolean }) {
  const date = new Date(`${due.due_date}T00:00:00Z`)
  return <details className="projection-due" open={expanded || undefined}>
    <summary aria-label={`${due.card_name}, due ${displayDate(due.due_date)}, ${money(due.currency, due.amount)}`}>
      <time className="projection-date" dateTime={due.due_date} aria-label={displayDate(due.due_date)}><span>{date.toLocaleDateString('en-US', { month: 'short', timeZone: 'UTC' })}</span><strong>{String(date.getUTCDate()).padStart(2, '0')}</strong></time>
      <div className="projection-due-title"><div><strong>{due.card_name}</strong>{due.plan_count > 0 && <span className="projection-plan-count"><Icon name="calendar" />{due.plan_count} payment {due.plan_count === 1 ? 'plan' : 'plans'}</span>}</div>
        <span className="projection-due-kind"><Icon name="wallet" />{due.currency === 'UNSPECIFIED' ? 'Entered card balance due' : 'Projected card due'}</span>
      </div>
      <strong className="projection-money projection-due-amount">{money(due.currency, due.amount)}</strong><span className="projection-chevron" aria-hidden="true" />
    </summary>
    <div className="projection-breakdown">
      <p className="projection-statement"><span>Statement closes <time dateTime={due.statement_close}>{displayDate(due.statement_close)}</time></span><span>Card payment due <time dateTime={due.due_date}>{displayDate(due.due_date)}</time></span></p>
      {due.installments.length > 0 && <div className="projection-table-wrap" role="region" aria-label={`${due.card_name} contributing installments`} tabIndex={0}><table className="projection-table">
        <caption className="sr-only">Provider installments contributing to this card due</caption><thead><tr><th scope="col">Included payment plans</th><th scope="col">Installment</th></tr></thead>
        <tbody>{due.installments.map(item => <tr key={`${item.plan_id}-${item.installment_number}`}><th scope="row"><span className="projection-bullet" aria-hidden="true" /><div><strong>{item.plan_name}</strong><span>{providerNames[item.provider_name as keyof typeof providerNames] || item.provider_name} · Installment {item.installment_number} of {item.installment_count}</span><span>Provider charge to card: <time dateTime={item.charge_date}>{displayDate(item.charge_date)}</time></span></div></th><td className="projection-money">{money(due.currency, item.amount)}</td></tr>)}</tbody>
      </table></div>}
      {due.currency === 'UNSPECIFIED' && <p className="projection-balance-note">Entered balance: <strong className="projection-money">{money(due.currency, due.balance_amount)}</strong>. Card balances have no saved currency and are kept separate from plan totals. The due date follows your entered balance date or the existing card schedule.</p>}
    </div>
    {due.installments.length > 0 && <footer><span>Total contributing installments</span><strong className="projection-money">{money(due.currency, due.contributing_total)}</strong></footer>}
  </details>
}

export function ProjectionScreen({ profileId, onAddCard, onAddPlan }: { profileId: string; onAddCard: () => void; onAddPlan: () => void }) {
  const [data, setData] = useState<Projection | null>(null)
  const [error, setError] = useState('')
  const [retry, setRetry] = useState(0)
  const [start, setStart] = useState('')
  const [months, setMonths] = useState(6)
  const [card, setCard] = useState('')
  const [currency, setCurrency] = useState('')
  const [choices, setChoices] = useState<Pick<Projection, 'cards' | 'currencies'> | null>(null)
  useEffect(() => {
    let cancelled = false
    setData(null); setError('')
    projectionApi.get(profileId, { start: start ? `${start}-01` : undefined, months, card_id: card, currency }).then(value => {
      if (!cancelled) { setData(value); setChoices(value) }
    }).catch(cause => { if (!cancelled) setError(cause instanceof Error ? cause.message : 'Could not calculate the projection.') })
    return () => { cancelled = true }
  }, [profileId, retry, start, months, card, currency])
  return <section className="projection-screen" aria-labelledby="projection-title">
    <div className="card-page-heading"><h1 id="projection-title">Cash Flow Projection</h1><p>How much money will I need, and when?</p></div>
    <details className="projection-options"><summary>Projection options</summary><div>
      <label>Start month<input type="month" value={start || data?.start_date.slice(0, 7) || ''} min="1900-01" max="9996-12" onChange={event => setStart(event.target.value)} /></label>
      <label>Period<select value={months} onChange={event => setMonths(Number(event.target.value))}>{[1, 3, 6, 12, 24].map(value => <option key={value} value={value}>{value} {value === 1 ? 'month' : 'months'}</option>)}</select></label>
      <label>Credit card<select value={card} onChange={event => setCard(event.target.value)}><option value="">All credit cards</option>{choices?.cards.map(item => <option key={item.id} value={item.id}>{item.name}</option>)}</select></label>
      <label>Currency<select value={currency} onChange={event => setCurrency(event.target.value)}><option value="">All currencies (separate totals)</option>{choices?.currencies.map(code => <option key={code} value={code}>{code}</option>)}<option value="UNSPECIFIED">Currency unspecified (card balances)</option></select></label>
      <button className="button secondary" onClick={() => setRetry(value => value + 1)}>Refresh projection</button>
    </div></details>
    {error ? <div className="error-panel" role="alert"><h2>Could not calculate projection</h2><p>{error}</p><button className="button secondary" onClick={() => setRetry(value => value + 1)}>Retry projection</button></div>
    : !data ? <p role="status">Calculating projection…</p>
    : data.card_count === 0 ? <div className="projection-empty"><h2>Add a credit card to get started</h2><p>Save a card’s statement and due dates to project your payment plans.</p><button className="button primary" onClick={onAddCard}>Add Credit Card</button></div>
    : <>
      {data.plan_count === 0 && <aside className="projection-empty"><h2>No payment plans yet</h2><p>Your entered card balances can be projected using their saved due dates or card schedules. Add a payment plan to include provider installments.</p><button className="button secondary" onClick={onAddPlan}>Add Payment Plan</button></aside>}
      {data.dues.length === 0 ? <div className="projection-empty"><h2>No card dues in this period</h2><p>Choose another period to see projected dues. Completed plans have no remaining installments.</p></div>
      : <div className="projection-months">{data.monthly.filter(month => month.dues.length > 0).map(month => <section className="projection-month" key={month.period} aria-label={month.period}>
        <header><h2>{new Date(`${month.period}-01T00:00:00Z`).toLocaleDateString('en-US', { month: 'long', year: 'numeric', timeZone: 'UTC' })}</h2><div><span>Total due</span><Amounts values={month.dues} /></div></header>
        <div className="projection-timeline">{data.dues.filter(due => due.due_date.startsWith(month.period)).map(due => <DueCard key={`${due.card_id}-${due.due_date}-${due.currency}`} due={due} expanded={due === data.dues[0]} />)}</div>
      </section>)}</div>}
      {!!data.charges?.length && <details className="projection-charge-schedule"><summary>Provider charges in the selected period</summary>
        <p>These installments charge your credit cards. Their card payment dues may fall in a later month.</p>
        <div className="projection-table-wrap" role="region" aria-label="Provider charge schedule" tabIndex={0}><table className="projection-table projection-charge-table"><caption className="sr-only">Provider charges, statement closes and card dues</caption><thead><tr>{['Plan / credit card', 'Provider charge date', 'Statement closes', 'Card payment due', 'Installment'].map(label => <th key={label} scope="col">{label}</th>)}</tr></thead><tbody>
          {data.charges.map(item => <tr key={`${item.plan_id}-${item.installment_number}`}><th scope="row"><div><strong>{item.plan_name}</strong><span>{item.card_name} · Installment {item.installment_number}</span></div></th><td>{displayDate(item.charge_date)}</td><td>{displayDate(item.statement_close)}</td><td>{displayDate(item.due_date)}</td><td className="projection-money">{money(item.currency, item.amount)}</td></tr>)}
        </tbody></table></div>
      </details>}
      <p className="projection-as-of">Calculated as of {displayDate(data.as_of_date)}. Provider charges, statement closing dates, and card dues are distinct events.</p>
    </>}
    <p className="projection-estimate">Estimates based on the information entered. No bank connection, automatic payments, or live account balances.</p>
  </section>
}
