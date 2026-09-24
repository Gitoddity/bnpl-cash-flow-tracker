type Name = 'wallet' | 'plus' | 'upload' | 'shield' | 'close' | 'add-circle' | 'arrow-left' | 'arrow-right' | 'info' | 'success' | 'calendar' | 'projection' | 'pencil'
export function Icon({ name }: { name: Name }) {
  const paths: Record<Name, React.ReactNode> = {
    pencil: <><path d="m16 3 5 5L9 20l-6 1 1-6L16 3ZM13 6l5 5"/></>,
    calendar: <><rect x="3" y="5" width="18" height="16" rx="2"/><path d="M7 3v4m10-4v4M3 11h18m-13 5h3m3 0h3"/></>,
    projection: <><path d="M3 3v18h18M7 15l5-5 4 3 5-8M16 5h5v5"/></>,
    success: <><circle cx="12" cy="12" r="9"/><path d="m8 12 3 3 5-6"/></>,
    'add-circle': <><circle cx="12" cy="12" r="9"/><path d="M12 8v8M8 12h8"/></>,
    'arrow-left': <path d="M20 12H4m6-6-6 6 6 6"/>,
    'arrow-right': <path d="M4 12h16m-6-6 6 6-6 6"/>,
    info: <><circle cx="12" cy="12" r="9"/><path d="M12 11v6m0-10v.01"/></>,
    wallet: <><path d="M20 8V5a2 2 0 0 0-2-2H5a3 3 0 0 0 0 6h15v11H5a3 3 0 0 1-3-3V6"/><path d="M20 12h-5v4h5"/><path d="M16 14h.01"/></>,
    plus: <path d="M12 5v14M5 12h14"/>,
    upload: <><path d="M14 2H5v20h14V7zM14 2v5h5"/><path d="M12 18v-7m-3 3 3-3 3 3"/></>,
    shield: <><path d="m12 3 8 3v6c0 5-8 9-8 9s-8-4-8-9V6z"/><path d="m8 12 3 3 5-6"/></>,
    close: <path d="m6 6 12 12M6 18 18 6"/>,
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[name]}</svg>
}
