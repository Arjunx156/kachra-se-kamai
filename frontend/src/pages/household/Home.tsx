import { lazy, Suspense } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../../api'
import { AiBadge } from '../../components/Badges'
import { KgSplitBar } from '../../components/KgSplitBar'
import { ScoreRing } from '../../components/ScoreRing'
import { ErrorState, Loading } from '../../components/States'
import { WalletCard } from '../../components/WalletCard'
import { dateTime, rs } from '../../lib/format'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'

const Mountain3D = lazy(() => import('../../components/Mountain3D'))

export default function Home() {
  const userId = userFor('household')
  const me = useApi(() => api.me(userId), [userId])
  const city = useApi(() => api.city(), [])

  if (me.loading && !me.data) return <Loading label="Opening your wallet…" />
  if (me.error && !me.data) return <ErrorState error={me.error} onRetry={me.reload} />
  if (!me.data) return null
  const d = me.data
  const latest = d.latestScan

  return (
    <div className="grid gap-4 md:grid-cols-2">
      <div className="flex flex-col gap-4">
        <h1 className="text-3xl font-bold">
          Namaste, {d.user.name} <span aria-hidden>👋</span>
        </h1>
        {d.society && <p className="-mt-3 text-slate/70">{d.society.name}, {d.society.area}</p>}
        <WalletCard me={d} />
        <Link to="/household/snap" className="btn-money min-h-[72px] text-2xl shadow-card">
          📸 Snap my bin
        </Link>
      </div>

      <div className="flex flex-col gap-4">
        <section className="card flex items-center gap-5">
          <ScoreRing score={d.avgScore} size={104} label="Avg. segregation" />
          <div className="flex-1">
            <div className="label">This week</div>
            <div className="num text-2xl">{d.week?.scans ?? 0} scans</div>
            {d.week && <KgSplitBar totals={d.week} showLegend={false} />}
            <p className="mt-2 text-sm text-slate/70">Separate wet and dry waste to push your score up, and your kamai with it.</p>
          </div>
        </section>

        <section className="card p-0">
          <div className="flex items-center justify-between px-5 pt-4">
            <h2 className="text-lg font-bold">Delhi's mountain</h2>
            <Link to="/city" className="text-sm font-semibold text-leaf">City view →</Link>
          </div>
          <Suspense fallback={<div className="h-44" />}>
            <Mountain3D compact heightFactor={city.data?.mountain.heightFactor ?? 1} className="mx-3 mb-3 mt-2 h-44" />
          </Suspense>
          <p className="px-5 pb-4 text-xs text-slate/60">Illustrative: the mountain shrinks as Delhi diverts waste on this platform.</p>
        </section>
      </div>

      {latest && (
        <Link to={`/household/result/${latest.scanId}`} className="card block md:col-span-2 hover:ring-2 hover:ring-leaf-200">
          <div className="flex items-center justify-between">
            <div>
              <div className="label">Latest scan · {dateTime(latest.createdAt)}</div>
              <div className="num text-2xl text-marigold-700">
                {rs(latest.finalRs ?? latest.estValueRs)} {latest.finalRs === undefined && <AiBadge />}
              </div>
            </div>
            <ScoreRing score={latest.segregationScore} size={64} label="Score" />
          </div>
          <div className="mt-3">
            <KgSplitBar totals={latest.totals} />
          </div>
          {latest.tip && <p className="mt-3 rounded-2xl bg-leaf-50 p-3 text-leaf">💡 {latest.tip}</p>}
        </Link>
      )}
    </div>
  )
}
