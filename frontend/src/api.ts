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
}
export type CardDraft = {
  name: string; current_balance: string; statement_end_day: string; payment_due_day: string
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
