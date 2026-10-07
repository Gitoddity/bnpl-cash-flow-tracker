import type { ReactNode } from 'react'

export const planIconNames = { shopping: 'Shopping bag', laptop: 'Laptop', home: 'Home', plane: 'Travel', car: 'Car', gift: 'Gift', heart: 'Heart', book: 'Book', phone: 'Phone', music: 'Music', coffee: 'Coffee', star: 'Star' } as const
export const planColors = { slate: 'Slate', blue: 'Blue', purple: 'Purple', pink: 'Pink', green: 'Green', orange: 'Orange' } as const
const paths: Record<keyof typeof planIconNames, ReactNode> = {
  shopping: <><path d="M5 7h14l1 14H4L5 7Z" /><path d="M8 8V6a4 4 0 0 1 8 0v2" /></>,
  laptop: <><rect x="4" y="3" width="16" height="13" rx="2" /><path d="M4 16 2 21h20l-2-5M9 19h6" /></>,
  home: <><path d="m3 10 9-7 9 7M5 9v12h14V9M9 21v-8h6v8" /></>,
  plane: <path d="m22 2-7 20-4-9-9-4 20-7ZM11 13 22 2" />,
  car: <><path d="m5 5-3 8v6h20v-6l-3-8H5ZM2 13h20M5 19v3m14-3v3M6 16h2m8 0h2" /></>,
  gift: <><rect x="3" y="8" width="18" height="4" rx="1" /><path d="M5 12v9h14v-9M12 8v13" /><path d="M12 8H8a3 3 0 1 1 3-3l1 3Zm0 0h4a3 3 0 1 0-3-3l-1 3Z" /></>,
  heart: <path d="M20 5a5 5 0 0 0-8 1 5 5 0 0 0-8-1c-5 5 3 12 8 16 5-4 13-11 8-16Z" />,
  book: <><path d="M12 5C9 3 5 3 2 4v16c3-1 7-1 10 1 3-2 7-2 10-1V4c-3-1-7-1-10 1v16" /></>,
  phone: <><rect x="6" y="2" width="12" height="20" rx="2" /><path d="M10 5h4M11 19h2" /></>,
  music: <><path d="M9 18V5l12-3v13M9 9l12-3" /><ellipse cx="6" cy="18" rx="3" ry="3" /><ellipse cx="18" cy="15" rx="3" ry="3" /></>,
  coffee: <><path d="M4 8h14v8a5 5 0 0 1-5 5H9a5 5 0 0 1-5-5V8ZM18 9h2a3 3 0 0 1 0 6h-2M7 2v3m5-3v3m5-3v3" /></>,
  star: <path d="m12 2 3 6 7 1-5 5 1 8-6-4-6 4 1-8-5-5 7-1 3-6Z" />,
}
export function PlanIcon({ icon = 'shopping', color = 'slate' }: { icon?: string; color?: string }) {
  const safeIcon = icon in planIconNames ? icon as keyof typeof planIconNames : 'shopping'
  const safeColor = color in planColors ? color : 'slate'
  return <span className={`plan-icon plan-color-${safeColor}`} aria-hidden="true"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">{paths[safeIcon]}</svg></span>
}
