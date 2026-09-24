// Presentation only. Python resolves the schedule; UTC prevents timezone shifts
// when rendering a date-only API value on a computer in another timezone.
const readableDate = new Intl.DateTimeFormat('en-US', { month: 'long', day: 'numeric', year: 'numeric', timeZone: 'UTC' })
export function displayDate(value: string): string {
  return readableDate.format(new Date(`${value}T00:00:00Z`))
}
