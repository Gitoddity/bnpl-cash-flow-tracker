import { apiBaseUrl, demoMode } from './hosting'

const sessionKey = 'duemap-demo-session'
let sessionToken: string | null = null
let sessionPromise: Promise<string> | null = null

function forgetSession() {
  sessionToken = null
  try { sessionStorage.removeItem(sessionKey) } catch { /* In-memory fallback. */ }
  window.dispatchEvent(new Event('duemap:session-ended'))
}

async function demoSession(): Promise<string> {
  if (!sessionToken) {
    try { sessionToken = sessionStorage.getItem(sessionKey) } catch { /* In-memory fallback. */ }
  }
  if (sessionToken) return sessionToken
  if (!sessionPromise) {
    sessionPromise = (async () => {
      const response = await fetch(`${apiBaseUrl}/api/session`, { method: 'POST' })
      if (!response.ok) throw new Error('The demo server is starting or busy. Please try again in a minute.')
      const body = await response.json()
      sessionToken = body.token
      if (typeof sessionToken !== 'string' || !sessionToken) throw new Error('Could not start a demo session. Please try again.')
      try { sessionStorage.setItem(sessionKey, sessionToken) } catch { /* In-memory fallback. */ }
      return sessionToken
    })().finally(() => { sessionPromise = null })
  }
  return sessionPromise
}

export type ProfileSummary = {
  id: string
  name: string
  card_count: number
  plan_count: number
}

export type ValidationIssue = { path: string; message: string }
export class ApiError extends Error {
  issues: ValidationIssue[]
  constructor(message: string, issues: ValidationIssue[] = []) {
    super(message)
    this.issues = issues
  }
}
export type Card = {
  id: string; profile_id: string; name: string; current_balance: string
  currency?: string
  statement_end_day: number; payment_due_day: number
  as_of_date: string; next_statement_close_date: string; next_payment_due_date: string
  upcoming_statement_close_date?: string; upcoming_statement_due_date?: string
  latest_statement_close_date: string; latest_statement_due_date: string; next_statement_due_date: string
}
export type CardDraft = {
  name: string; current_balance: string; upcoming_statement_close_date: string; upcoming_statement_due_date: string
  currency?: string
}

async function requestResponse(path: string, init?: RequestInit): Promise<Response> {
  let response: Response
  try {
    let options = init
    if (demoMode) {
      const headers = new Headers(init?.headers)
      headers.set('X-DueMap-Session', await demoSession())
      options = { ...init, headers }
    }
    response = await fetch(`${apiBaseUrl}/api${path}`, options)
  } catch {
    throw new Error(demoMode
      ? 'Cannot reach the demo server. It may be waking up. Please try again in a minute.'
      : 'Cannot reach the local server. Check that FastAPI is running and try again.')
  }
  if (demoMode && response.status === 410) forgetSession()
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    if (response.status === 404 && body?.detail === 'Not Found' && path.includes('/projection?')) {
      throw new ApiError('The running local API does not have the Projection endpoint. Restart the DueMap API, then retry projection.')
    }
    const issues = body?.issues?.map((item: { path: string; message: string }) => `${item.path}: ${item.message}`).join(' • ')
    throw new ApiError(issues || body?.detail || 'The server could not complete this request. Please try again.', body?.issues || [])
  }
  return response
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  return (await requestResponse(path, init)).json() as Promise<T>
}

export const exportProfileUrl = (profileId: string) => `${apiBaseUrl}/api/profiles/${encodeURIComponent(profileId)}/export`

export const profilesApi = {
  exportUrl: exportProfileUrl,
  download: async (profileId: string) => {
    const response = await requestResponse(`/profiles/${encodeURIComponent(profileId)}/export`)
    const url = URL.createObjectURL(await response.blob())
    const link = document.createElement('a')
    link.href = url
    link.download = 'duemap-profile.json'
    document.body.appendChild(link)
    link.click()
    link.remove()
    window.setTimeout(() => URL.revokeObjectURL(url), 1000)
  },
  list: () => request<ProfileSummary[]>('/profiles'),
  create: (name: string) => request<ProfileSummary>('/profiles', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ name }),
  }),
  // Upload original bytes. JSON parsing and financial validation belong to Python.
  import: (file: File) => request<ProfileSummary>('/profiles/import', {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: file,
  }),
}

export const cardsApi = {
  update: (profileId: string, cardId: string, card: CardDraft) => request<Card>(`/profiles/${encodeURIComponent(profileId)}/cards/${encodeURIComponent(cardId)}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(card),
  }),
  list: (profileId: string) => request<Card[]>(`/profiles/${encodeURIComponent(profileId)}/cards`),
  create: (profileId: string, card: CardDraft) => request<Card>(`/profiles/${encodeURIComponent(profileId)}/cards`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(card),
  }),
}

export const providerNames = { paypal: 'PayPal', klarna: 'Klarna', afterpay: 'Afterpay', sezzle: 'Sezzle', affirm: 'Affirm' } as const
export type PlanDraft = {
  icon?: string; icon_color?: string
  plan_name: string; provider_name: string; credit_card_id: string; purchase_amount: string; currency: string
  purchase_date: string; first_installment_date: string; installment_count: string; paid_installment_count: string
}
export type PaymentPlan = Omit<PlanDraft, 'installment_count' | 'paid_installment_count'> & {
  id: string; installment_count: number; paid_installment_count: number; installment_frequency: 'BIWEEKLY'; amount_paid: string
}
export type PlanRow = PaymentPlan & { credit_card_name: string; remaining_installment_count: number; completed: boolean; remaining_amount: string; progress_percent: number }
export type CurrencyAmount = { currency: string; amount: string }
export type ProjectionInstallment = {
  plan_id: string; plan_name: string; provider_name: string; installment_number: number
  installment_count: number; charge_date: string; amount: string
}
export type ProjectionDue = {
  card_id: string; card_name: string; statement_start: string; statement_close: string
  due_date: string; currency: string; amount: string; balance_amount: string
  installment_count: number; plan_count: number; contributing_total: string; installments: ProjectionInstallment[]
}
export type Projection = {
  as_of_date: string; start_date: string; end_date: string; months: number; card_count: number; plan_count: number
  cards: { id: string; name: string }[]; currencies: string[]
  monthly: { period: string; charges: CurrencyAmount[]; dues: CurrencyAmount[] }[]
  dues: ProjectionDue[]
  charges?: { plan_id: string; plan_name: string; provider_name: string; card_id: string; card_name: string; installment_number: number; charge_date: string; statement_close: string; due_date: string; currency: string; amount: string }[]
}
export const projectionApi = {
  get: (profileId: string, options: { start?: string; months?: number; card_id?: string; currency?: string } = {}) => {
    const query = new URLSearchParams()
    for (const [key, value] of Object.entries(options)) if (value !== undefined && value !== '') query.set(key, String(value))
    return request<Projection>(`/profiles/${encodeURIComponent(profileId)}/projection?${query}`)
  },
}
export type PlanOverview = { plans: PlanRow[]; summary: { active_plans: number; remaining_totals: CurrencyAmount[]; next_charge: { date: string; amounts: CurrencyAmount[] } | null } }
export const plansApi = {
  overview: (profileId: string) => request<PlanOverview>(`/profiles/${encodeURIComponent(profileId)}/plans/overview`),
  update: (profileId: string, planId: string, draft: PlanDraft) => request<PaymentPlan>(`/profiles/${encodeURIComponent(profileId)}/plans/${encodeURIComponent(planId)}`, {
    method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, installment_frequency: 'BIWEEKLY' }),
  }),
  delete: (profileId: string, planId: string) => request<{ deleted: boolean }>(`/profiles/${encodeURIComponent(profileId)}/plans/${encodeURIComponent(planId)}`, { method: 'DELETE' }),
  list: (profileId: string) => request<PaymentPlan[]>(`/profiles/${encodeURIComponent(profileId)}/plans`),
  create: (profileId: string, draft: PlanDraft) => request<PaymentPlan>(`/profiles/${encodeURIComponent(profileId)}/plans`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, installment_frequency: 'BIWEEKLY' }),
  }),
}
