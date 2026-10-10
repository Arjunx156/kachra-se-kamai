import { Link, useLocation, useParams } from 'react-router-dom'
import { api } from '../../api'
import { AiBadge, DemoBadge } from '../../components/Badges'
import { KgSplitBar } from '../../components/KgSplitBar'
import { MaterialChip } from '../../components/MaterialChip'
import { ScoreRing } from '../../components/ScoreRing'
import { ErrorState, Loading } from '../../components/States'
import { dateTime, kg, rs } from '../../lib/format'
import { EPR_MATERIALS, material } from '../../lib/materials'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'
import type { Scan } from '../../types'

const EPR_RS_PER_PACKET = 0.5 // DEMO: simulated EPR partner, mirrors backend config

function brandGroups(scan: Scan) {
  return scan.items
    .filter((it) => it.brand && EPR_MATERIALS.includes(it.material))
    .map((it) => ({ key: `${it.brand}-${it.material}`, count: it.count, brand: it.brand!, label: material(it.material).en.toLowerCase(), rs: it.count * EPR_RS_PER_PACKET }))
}

function StatusLine({ scan }: { scan: Scan }) {
  const where = scan.societyName ?? 'your society'
  if (scan.status === 'collected')
    return <p className="rounded-2xl bg-leaf-50 p-3 font-semibold text-leaf">✓ Collected. {rs((scan.finalRs ?? 0) + (scan.eprCreditedRs ?? 0))} credited to your wallet.</p>
  if (scan.status === 'bundled') return <p className="rounded-2xl bg-marigold-50 p-3 font-semibold text-marigold-700">🛺 In tonight's pickup from {where}.</p>
  if (scan.status === 'no_recyclables') return <p className="rounded-2xl bg-cream-200 p-3">No recyclables to pick up this time.</p>
  return <p className="rounded-2xl bg-marigold-50 p-3 font-semibold text-marigold-700">🛺 Added to tonight's pickup from {where}.</p>
}

export default function Result() {
  const { scanId = '' } = useParams()
  const location = useLocation() as { state?: { scan?: Scan; preview?: string } }
  const userId = userFor('household')
  const fresh = location.state?.scan?.scanId === scanId ? location.state.scan : undefined
  const res = useApi(() => (fresh ? Promise.resolve(fresh) : api.scan(userId, scanId)), [scanId])

  if (res.loading && !res.data) return <Loading label="Loading your result…" />
  if (res.error && !res.data) return <ErrorState error={res.error} onRetry={res.reload} />
  const scan = res.data
  if (!scan) return null
  const photo = location.state?.preview ?? scan.imageUrl
  const brands = brandGroups(scan)

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div className="flex items-baseline justify-between">
        <h1 className="text-3xl font-bold">Your bin</h1>
        <span className="text-sm text-slate/60">{dateTime(scan.createdAt)}</span>
      </div>

      {photo && <img src={photo} alt="Your bin" className="max-h-80 w-full rounded-3xl object-cover shadow-card" />}

      <section className="card bg-marigold-50">
        <div className="flex flex-wrap items-center gap-2">
          <span className="label">You could earn</span> <AiBadge /> <DemoBadge label="Demo rates" />
        </div>
        <div className="num mt-1 text-5xl text-marigold-700">{rs(scan.estValueRs)}</div>
        <p className="text-sm text-slate/70">Your 60% share of the recyclables at today's rates. The final amount is set when the picker weighs it at pickup.</p>
      </section>

      <section className="card">
        <div className="mb-3 flex items-center justify-between">
          <h2 className="text-xl font-bold">Where it's going</h2>
          <AiBadge />
        </div>
        <KgSplitBar totals={scan.totals} />
      </section>

      <section className="card">
        <h2 className="mb-3 text-xl font-bold">What the AI found</h2>
        {scan.items.length === 0 ? (
          <p className="text-slate/70">The AI couldn't make out individual items. Try a closer photo in good light.</p>
        ) : (
          <ul className="divide-y divide-cream-200">
            {scan.items.map((it, i) => (
              <li key={i} className="flex items-center justify-between gap-3 py-2.5">
                <div className="min-w-0">
                  <div className="truncate font-semibold capitalize">
                    {it.count > 1 && <span className="text-slate/60">{it.count}× </span>}
                    {it.name}
                    {it.brand && <span className="ml-1 text-sm font-normal text-slate/60">({it.brand})</span>}
                  </div>
                  <MaterialChip code={it.material} />
                </div>
                <span className="num text-lg">{kg(it.estWeightKg)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>

      {brands.length > 0 && (
        <section className="card">
          <div className="mb-2 flex flex-wrap items-center gap-2">
            <h2 className="text-xl font-bold">Brand rewards</h2>
            <DemoBadge label="Simulated EPR partner" />
          </div>
          <ul className="flex flex-col gap-1.5">
            {brands.map((b) => (
              <li key={b.key} className="flex justify-between">
                <span>
                  {b.count} {b.brand} {b.label}
                </span>
                <span className="num text-marigold-700">→ {rs(b.rs)}</span>
              </li>
            ))}
          </ul>
          <p className="mt-2 border-t border-cream-200 pt-2 font-semibold">
            Total {rs(scan.eprRs)} brand reward{scan.eprRs >= 10 ? ' (capped at ₹10 per scan)' : ''}, credited at pickup.
          </p>
        </section>
      )}

      <section className="card flex items-center gap-4">
        <ScoreRing score={scan.segregationScore} size={96} label="Segregation" />
        <div className="flex-1">
          <div className="flex items-center gap-2">
            <span className="label">AI tip</span> <AiBadge />
          </div>
          <p className="mt-1 text-lg">💡 {scan.tip || 'Keep wet and dry waste in separate bins.'}</p>
        </div>
      </section>

      <StatusLine scan={scan} />

      <div className="flex gap-3">
        <Link to="/household" className="btn-ghost flex-1">Home</Link>
        <Link to="/household/snap" className="btn-primary flex-1">Snap another</Link>
      </div>
    </div>
  )
}
