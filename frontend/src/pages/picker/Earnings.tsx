import { api } from '../../api'
import { DemoBadge } from '../../components/Badges'
import { ErrorState, Loading } from '../../components/States'
import { dateTime, isToday, kg, rs } from '../../lib/format'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'

export default function Earnings() {
  const pickerId = userFor('picker')
  const me = useApi(() => api.me(pickerId), [pickerId])
  const done = useApi(() => api.bundles('collected', pickerId), [pickerId])

  if ((me.loading && !me.data) || (done.loading && !done.data)) return <Loading label="Loading earnings…" />
  const err = me.error ?? done.error
  if (err && (!me.data || !done.data)) return <ErrorState error={err} onRetry={() => { me.reload(); done.reload() }} />

  const bundles = done.data?.bundles ?? []
  const today = bundles.filter((b) => isToday(b.collectedAt))
  const todayRs = today.reduce((s, b) => s + (b.pickerRs ?? 0), 0)
  const w = me.data!.wallet

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-3xl font-bold">Earnings</h1>
      <section className="card bg-leaf text-white">
        <div className="text-sm uppercase tracking-wider text-white/70">Today</div>
        <div className="num text-6xl text-marigold">{rs(todayRs)}</div>
        <div className="text-white/80">{today.length} pickups today</div>
      </section>
      <section className="grid grid-cols-3 gap-3 text-center">
        <div className="card p-4"><div className="num text-2xl">{rs(w.pickerPayoutRs)}</div><div className="label">all time</div></div>
        <div className="card p-4"><div className="num text-2xl">{w.pickupCount}</div><div className="label">pickups</div></div>
        <div className="card p-4"><div className="num text-2xl">{kg(w.divertedKg)}</div><div className="label">collected</div></div>
      </section>
      <p className="text-sm text-slate/60">Guaranteed 40% of each bundle's value at the recycler's posted rates. <DemoBadge label="Demo split" /></p>
      <section className="card">
        <h2 className="mb-2 text-xl font-bold">Recent pickups</h2>
        {bundles.length === 0 ? (
          <p className="text-slate/70">No pickups yet.</p>
        ) : (
          <ul className="divide-y divide-cream-200">
            {bundles.slice(0, 15).map((b) => (
              <li key={b.bundleId} className="flex items-center justify-between py-2.5">
                <div>
                  <div className="font-semibold">{b.societyName}</div>
                  <div className="text-sm text-slate/60">{b.collectedAt ? dateTime(b.collectedAt) : ''} · {kg(b.totalKg)}</div>
                </div>
                <span className="num text-xl text-marigold-700">{rs(b.pickerRs)}</span>
              </li>
            ))}
          </ul>
        )}
      </section>
    </div>
  )
}
