import { kg } from '../lib/format'
import { CATEGORY_STYLE } from '../lib/materials'
import type { Totals } from '../types'

const ORDER = [
  ['recyclableKg', 'recyclable'],
  ['compostableKg', 'compostable'],
  ['landfillKg', 'landfill'],
] as const

export function KgSplitBar({ totals, showLegend = true }: { totals: Totals; showLegend?: boolean }) {
  const total = totals.recyclableKg + totals.compostableKg + totals.landfillKg
  return (
    <div>
      <div
        className="flex h-4 w-full overflow-hidden rounded-full bg-cream-200"
        role="img"
        aria-label={`Recyclable ${kg(totals.recyclableKg)}, compostable ${kg(totals.compostableKg)}, landfill ${kg(totals.landfillKg)}`}
      >
        {total > 0 &&
          ORDER.map(([key, cat]) => {
            const pct = (totals[key] / total) * 100
            return pct > 0 ? <div key={key} className={`${CATEGORY_STYLE[cat].bar} h-full`} style={{ width: `${pct}%` }} /> : null
          })}
      </div>
      {showLegend && (
        <div className="mt-2 grid grid-cols-3 gap-2 text-sm">
          {ORDER.map(([key, cat]) => (
            <div key={key}>
              <div className="flex items-center gap-1.5">
                <span className={`h-2.5 w-2.5 rounded-full ${CATEGORY_STYLE[cat].bar}`} />
                <span className="text-slate/70">{CATEGORY_STYLE[cat].label}</span>
              </div>
              <div className={`num text-lg ${CATEGORY_STYLE[cat].text}`}>{kg(totals[key])}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
