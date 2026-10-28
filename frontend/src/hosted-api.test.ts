import { afterEach, beforeEach, expect, test, vi } from 'vitest'

beforeEach(() => {
  vi.resetModules()
  sessionStorage.clear()
  vi.stubEnv('VITE_DEMO_MODE', 'true')
  vi.stubEnv('VITE_API_BASE_URL', 'https://demo.example')
})
afterEach(() => { vi.unstubAllEnvs(); vi.unstubAllGlobals(); sessionStorage.clear() })

function json(body: unknown, status = 200) {
  return new Response(JSON.stringify(body), { status, headers: { 'Content-Type': 'application/json' } })
}

test('concurrent calls share one session and never put its token in a URL', async () => {
  const fetch = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(json({ token: 'secret-session' }, 201))
    .mockImplementation(async () => json([]))
  const { profilesApi } = await import('./api')
  await Promise.all([profilesApi.list(), profilesApi.list()])
  expect(fetch).toHaveBeenCalledTimes(3)
  expect(fetch.mock.calls[0]).toEqual(['https://demo.example/api/session', { method: 'POST' }])
  for (const [url, init] of fetch.mock.calls.slice(1)) {
    expect(url).toBe('https://demo.example/api/profiles')
    expect(new Headers(init?.headers).get('X-DueMap-Session')).toBe('secret-session')
  }
})

test('profile import and download keep the visitor identity and preserve the file', async () => {
  sessionStorage.setItem('duemap-demo-session', 'existing-session')
  const source = { format: 'bnpl-profile', version: 1, profile: { id: 'personal', name: 'Personal' } }
  const fetch = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(json({ id: 'personal' }, 201))
    .mockResolvedValueOnce(json(source))
  const createObjectURL = vi.fn(() => 'blob:profile')
  vi.stubGlobal('URL', class extends URL {
    static createObjectURL = createObjectURL
    static revokeObjectURL = vi.fn()
  })
  const click = vi.spyOn(HTMLAnchorElement.prototype, 'click').mockImplementation(() => {})
  const { profilesApi } = await import('./api')
  const file = new File([JSON.stringify(source)], 'profile.json', { type: 'application/json' })
  await profilesApi.import(file)
  await profilesApi.download('personal')
  expect(fetch.mock.calls[0][1]?.body).toBe(file)
  expect(new Headers(fetch.mock.calls[0][1]?.headers).get('Content-Type')).toBe('application/json')
  expect(fetch.mock.calls[1][0]).toBe('https://demo.example/api/profiles/personal/export')
  expect(new Headers(fetch.mock.calls[1][1]?.headers).get('X-DueMap-Session')).toBe('existing-session')
  expect(createObjectURL).toHaveBeenCalledWith(expect.any(Blob))
  expect(click).toHaveBeenCalledOnce()
  expect((click.mock.instances[0] as HTMLAnchorElement).download).toBe('duemap-profile.json')
})

test('a restarted server clears the stale session and allows a fresh import', async () => {
  sessionStorage.setItem('duemap-demo-session', 'expired-session')
  const ended = vi.fn()
  window.addEventListener('duemap:session-ended', ended)
  const fetch = vi.spyOn(globalThis, 'fetch')
    .mockResolvedValueOnce(json({ detail: 'Your temporary session ended.' }, 410))
    .mockResolvedValueOnce(json({ token: 'new-session' }, 201))
    .mockResolvedValueOnce(json([]))
  try {
    const { profilesApi } = await import('./api')
    await expect(profilesApi.list()).rejects.toThrow('Your temporary session ended.')
    expect(ended).toHaveBeenCalledOnce()
    expect(sessionStorage.getItem('duemap-demo-session')).toBeNull()
    expect(await profilesApi.list()).toEqual([])
    expect(fetch.mock.calls[1][0]).toBe('https://demo.example/api/session')
  } finally {
    window.removeEventListener('duemap:session-ended', ended)
  }
})
