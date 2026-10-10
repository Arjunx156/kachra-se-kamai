const rupee = new Intl.NumberFormat('en-IN', { style: 'currency', currency: 'INR', minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const rs = (n: number | undefined | null) => rupee.format(n ?? 0)

export function kg(n: number | undefined | null): string {
  const v = n ?? 0
  if (v > 0 && v < 1) return `${Math.round(v * 1000)} g`
  return `${v.toLocaleString('en-IN', { maximumFractionDigits: 2 })} kg`
}

export function dateTime(iso: string): string {
  const d = new Date(iso)
  return d.toLocaleString('en-IN', { day: 'numeric', month: 'short', hour: 'numeric', minute: '2-digit' })
}

export function isToday(iso: string | undefined, now = new Date()): boolean {
  if (!iso) return false
  const d = new Date(iso)
  return d.getFullYear() === now.getFullYear() && d.getMonth() === now.getMonth() && d.getDate() === now.getDate()
}
