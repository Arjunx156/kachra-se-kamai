import { CATEGORY_STYLE, material } from '../lib/materials'

export function MaterialChip({ code, hindi = false }: { code: string; hindi?: boolean }) {
  const m = material(code)
  const style = CATEGORY_STYLE[m.category]
  return (
    <span className={`inline-flex items-center gap-1.5 rounded-full px-3 py-1 text-sm font-semibold ${style.bg} ${style.text}`}>
      <span aria-hidden>{m.emoji}</span>
      {hindi ? m.hi : m.en}
    </span>
  )
}
