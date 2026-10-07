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
  statement_end_day: number; payment_due_day: number
  as_of_date: string; next_statement_close_date: string; next_payment_due_date: string
  upcoming_statement_close_date?: string; upcoming_statement_due_date?: string
  latest_statement_close_date: string; latest_statement_due_date: string; next_statement_due_date: string
}
export type CardDraft = {
  name: string; current_balance: string; upcoming_statement_close_date: string; upcoming_statement_due_date: string
}

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  let response: Response
  try {
    response = await fetch(`/api${path}`, init)
  } catch {
    throw new Error('Cannot reach the local server. Check that FastAPI is running and try again.')
  }
  const body = await response.json().catch(() => null)
  if (!response.ok) {
    const issues = body?.issues?.map((item: { path: string; message: string }) => `${item.path}: ${item.message}`).join(' • ')
    throw new ApiError(issues || body?.detail || 'The local server could not complete this request. Please try again.', body?.issues || [])
  }
  return body as T
}

export const profilesApi = {
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
  plan_name: string; provider_name: string; credit_card_id: string; purchase_amount: string; currency: string
  purchase_date: string; first_installment_date: string; installment_count: string; paid_installment_count: string
}
export type PaymentPlan = Omit<PlanDraft, 'installment_count' | 'paid_installment_count'> & {
  id: string; installment_count: number; paid_installment_count: number; installment_frequency: 'BIWEEKLY'; amount_paid: string
}
export const plansApi = {
  list: (profileId: string) => request<PaymentPlan[]>(`/profiles/${encodeURIComponent(profileId)}/plans`),
  create: (profileId: string, draft: PlanDraft) => request<PaymentPlan>(`/profiles/${encodeURIComponent(profileId)}/plans`, {
    method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ ...draft, installment_frequency: 'BIWEEKLY' }),
  }),
}
