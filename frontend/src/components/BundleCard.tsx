import { Link } from 'react-router-dom'
import { kg, rs } from '../lib/format'
import type { Bundle } from '../types'
import { DemoBadge } from './Badges'
import { MaterialChip } from './MaterialChip'

interface Props {
  bundle: Bundle
  onAccept?: (b: Bundle) => void
  busy?: boolean
}

export function BundleCard({ bundle: b, onAccept, busy }: Props) {
  const materials = Object.entries(b.materials).sort((a, z) => (z[1] ?? 0) - (a[1] ?? 0))
  return (
    <article className="card flex flex-col gap-3">
      <header className="flex items-start gap-3">
        {b.routeOrder !== undefined && (
          <span className="num flex h-10 w-10 shrink-0 items-center justify-center rounded-full bg-leaf text-xl text-white" aria-label={`Stop ${b.routeOrder}`}>
            {b.routeOrder}
          </span>
        )}
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-xl font-bold leading-tight">{b.societyName}</h3>
          <div className="text-slate/70">
            {b.area} · {b.householdCount} {b.householdCount === 1 ? 'home' : 'homes'}
            {b.distanceKmFromPrev !== undefined && <> · {b.distanceKmFromPrev.toFixed(1)} km</>}
          </div>
        </div>
        <div className="text-right">
          <div className="label">Your share</div>
          <div className="num text-3xl text-marigold-700">{rs(b.pickerShareRs)}</div>
        </div>
      </header>
      <div className="flex flex-wrap gap-2">
        {materials.map(([code, w]) => (
          <span key={code} className="inline-flex items-center gap-1">
            <MaterialChip code={code} /> <span className="num text-sm">{kg(w)}</span>
          </span>
        ))}
      </div>
      <div className="flex items-center justify-between border-t border-cream-200 pt-3 text-slate/70">
        <span>
          <span className="num text-lg text-slate">{kg(b.totalKg)}</span> total · bundle value {rs(b.valueRs)} <DemoBadge label="Demo rates" />
        </span>
      </div>
      <div className="flex gap-3">
        <Link to={`/picker/bundle/${b.bundleId}`} className="btn-ghost flex-1">
          Details
        </Link>
        {onAccept && b.status === 'open' && (
          <button className="btn-primary flex-[2]" disabled={busy} onClick={() => onAccept(b)}>
            {busy ? 'Accepting…' : '✋ Accept'}
          </button>
        )}
      </div>
    </article>
  )
}
