import { api } from '../../api'
import { MaterialChip } from '../../components/MaterialChip'
import { Empty, ErrorState, Loading } from '../../components/States'
import { dateTime, kg, rs } from '../../lib/format'
import { useApi } from '../../lib/useApi'

export default function Incoming() {
  const res = useApi(() => api.bundles('collected'), [])
  if (res.loading && !res.data) return <Loading label="Loading incoming supply…" />
  if (res.error && !res.data) return <ErrorState error={res.error} onRetry={res.reload} />
  const bundles = res.data?.bundles ?? []

  const totals: Record<string, number> = {}
  bundles.forEach((b) => Object.entries(b.materials).forEach(([m, w]) => (totals[m] = (totals[m] ?? 0) + (w ?? 0))))
  const sorted = Object.entries(totals).sort((a, z) => z[1] - a[1])

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-3xl font-bold">Incoming supply</h1>
      {bundles.length === 0 ? (
        <Empty icon="♻️" title="Nothing collected yet" />
      ) : (
        <>
          <section className="card">
            <h2 className="mb-2 text-xl font-bold">Pre-sorted totals</h2>
            <ul className="grid grid-cols-2 gap-x-6 gap-y-2 md:grid-cols-3">
              {sorted.map(([m, w]) => (
                <li key={m} className="flex items-center justify-between">
                  <MaterialChip code={m} /> <span className="num">{kg(w)}</span>
                </li>
              ))}
            </ul>
          </section>
          <ul className="grid gap-3 md:grid-cols-2">
            {bundles.map((b) => (
              <li key={b.bundleId} className="card">
                <div className="flex justify-between">
                  <div>
                    <div className="font-bold">{b.societyName}</div>
                    <div className="text-sm text-slate/60">{b.collectedAt ? dateTime(b.collectedAt) : ''} · {b.householdCount} homes</div>
                  </div>
                  <div className="text-right">
                    <div className="num text-xl">{kg(b.totalKg)}</div>
                    <div className="text-sm text-slate/60">{rs(b.valueRs)}</div>
                  </div>
                </div>
              </li>
            ))}
          </ul>
        </>
      )}
    </div>
  )
}
