import type { ProfileSummary } from './api'
import { Icon } from './Icon'

export function ProfileEmptyState({ profile, onAdd }: { profile: ProfileSummary; onAdd: () => void }) {
  return <section className="landing profile-workspace" aria-labelledby="profile-title">
    <p className="active-profile-label">Active profile</p>
    <h1 id="profile-title" tabIndex={-1}>{profile.name}</h1>
    <div className="wallet-mark"><Icon name="wallet" /></div>
    <h2>{profile.card_count === 0 ? 'Add your first credit card' : 'Your profile is ready'}</h2>
    <p className="intro">{profile.card_count === 0
      ? 'Start with the credit card you use for your installment plans.'
      : `${profile.card_count} cards · ${profile.plan_count} payment plans saved in this profile.`}</p>
    <div className="landing-actions"><button className="button primary" onClick={onAdd}><Icon name="plus" />Add Credit Card</button></div>
  </section>
}
