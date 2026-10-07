import { useEffect, useRef, useState, type KeyboardEvent } from 'react'
import { providerNames } from './api'
import { ProviderBadge } from './ProviderBadge'

const providers = Object.keys(providerNames) as (keyof typeof providerNames)[]

export function ProviderSelect({ id, value, disabled, invalid, describedBy, onChange }: {
  id: string; value: string; disabled: boolean; invalid: boolean; describedBy: string; onChange: (provider: string) => void
}) {
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const root = useRef<HTMLDivElement>(null)
  const trigger = useRef<HTMLButtonElement>(null)
  const listId = `${id}-options`
  function show(index = Math.max(0, providers.indexOf(value as keyof typeof providerNames))) {
    setActive(index); setOpen(true)
  }
  function choose(index: number) {
    onChange(providers[index]); setOpen(false); trigger.current?.focus()
  }
  useEffect(() => {
    if (!open) return
    function outside(event: PointerEvent) {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', outside)
    return () => document.removeEventListener('pointerdown', outside)
  }, [open])
  useEffect(() => { if (disabled) setOpen(false) }, [disabled])
  useEffect(() => {
    if (open) document.getElementById(`${listId}-${active}`)?.scrollIntoView?.({ block: 'nearest' })
  }, [open, active, listId])
  function keyDown(event: KeyboardEvent<HTMLButtonElement>) {
    if (disabled) return
    if (event.key === 'Tab') { setOpen(false); return }
    if (event.key === 'Escape') { event.preventDefault(); setOpen(false); return }
    if (event.key === 'ArrowDown' || event.key === 'ArrowUp') {
      event.preventDefault()
      if (!open) show()
      else setActive(index => (index + (event.key === 'ArrowDown' ? 1 : providers.length - 1)) % providers.length)
    } else if (event.key === 'Home' || event.key === 'End') {
      event.preventDefault(); show(event.key === 'Home' ? 0 : providers.length - 1)
    } else if (event.key === 'Enter' || event.key === ' ') {
      event.preventDefault(); if (open) choose(active); else show()
    } else if (/^[a-z]$/i.test(event.key)) {
      const index = providers.findIndex(provider => providerNames[provider].toLowerCase().startsWith(event.key.toLowerCase()))
      if (index !== -1) { event.preventDefault(); show(index) }
    }
  }
  return <div ref={root} className="provider-select" onBlur={event => {
    if (!event.currentTarget.contains(event.relatedTarget)) setOpen(false)
  }}>
    <input type="hidden" name="provider_name" value={value} />
    <button ref={trigger} id={id} type="button" role="combobox" aria-haspopup="listbox" aria-expanded={open}
      aria-controls={open ? listId : undefined} aria-activedescendant={open ? `${listId}-${active}` : undefined}
      aria-required="true" aria-invalid={invalid} aria-describedby={describedBy} disabled={disabled}
      onClick={() => open ? setOpen(false) : show()} onKeyDown={keyDown}>
      {value ? <ProviderBadge provider={value} /> : <span className="provider-placeholder">Select a provider</span>}
      <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7"><path d="m6 9 6 6 6-6" /></svg>
    </button>
    {open && <ul id={listId} role="listbox" aria-label="Payment Plan Provider" className="provider-options">
      {providers.map((provider, index) => <li key={provider} id={`${listId}-${index}`} role="option" tabIndex={-1} aria-selected={provider === value}
        className={active === index ? 'provider-option-active' : ''} onMouseDown={event => event.preventDefault()}
        onPointerMove={() => setActive(index)} onClick={() => choose(index)}>
        <ProviderBadge provider={provider} />{provider === value && <span aria-hidden="true">✓</span>}
      </li>)}
    </ul>}
  </div>
}
