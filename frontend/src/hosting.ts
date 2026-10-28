export const demoMode = import.meta.env.VITE_DEMO_MODE === 'true'
export const apiBaseUrl = (import.meta.env.VITE_API_BASE_URL || '').replace(/\/+$/, '')

export const storageDescription = demoMode
  ? 'Profiles are temporary and expire after 30 minutes without activity, or when the demo server restarts. Download your profile to save your changes, then import it next time.'
  : 'Profiles are saved on this computer by the local server. Closing this tab won’t delete them. Use Export Profile to download a portable backup.'
