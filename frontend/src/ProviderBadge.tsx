import { providerNames } from './api'

export function ProviderBadge({ provider }: { provider: string }) {
  const key = provider.toLowerCase() as keyof typeof providerNames
  if (!(key in providerNames)) return <span>{provider}</span>
  return <span className="provider-badge"><span className={`provider-mark provider-${key}`}><img src={`${import.meta.env.BASE_URL}providers/${key}.${key === 'affirm' ? 'png' : 'svg'}`} alt="" aria-hidden="true" width="20" height="20" /></span><span>{providerNames[key]}</span></span>
}
