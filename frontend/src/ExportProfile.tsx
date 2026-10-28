import { useState } from 'react'
import { exportProfileUrl, profilesApi } from './api'

export function ExportProfile({ profileId, className }: { profileId: string; className?: string }) {
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  return <span>
    <a className={className} href={exportProfileUrl(profileId)} download="duemap-profile.json"
      aria-disabled={busy} onClick={async event => {
        event.preventDefault()
        if (busy) return
        setBusy(true); setError('')
        try { await profilesApi.download(profileId) }
        catch (cause) { setError(cause instanceof Error ? cause.message : 'Download failed. Please try again.') }
        finally { setBusy(false) }
      }}>{busy ? 'Downloading…' : 'Export Profile'}</a>
    {error && <span className="error" role="alert">{error}</span>}
  </span>
}
