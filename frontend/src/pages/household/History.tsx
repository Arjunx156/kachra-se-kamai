import { Link } from 'react-router-dom'
import { api } from '../../api'
import { KgSplitBar } from '../../components/KgSplitBar'
import { ScoreRing } from '../../components/ScoreRing'
import { Empty, ErrorState, Loading } from '../../components/States'
import { dateTime, rs } from '../../lib/format'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'
import type { Scan } from '../../types'

function Status({ scan }: { scan: Scan }) {
  switch (scan.status) {
    case 'collected':
      return <span className="rounded-full bg-leaf-50 px-3 py-1 text-sm font-semibold text-leaf">Collected ✓ {rs((scan.finalRs ?? 0) + (scan.eprCreditedRs ?? 0))}</span>
    case 'bundled':
      return <span className="rounded-full bg-marigold-50 px-3 py-1 text-sm font-semibold text-marigold-700">In pickup</span>
    case 'no_recyclables':
      return <span className="rounded-full bg-cream-200 px-3 py-1 text-sm font-semibold text-slate/70">Nothing to collect</span>
    default:
      return <span className="rounded-full bg-cream-200 px-3 py-1 text-sm font-semibold">Pending · ~{rs(scan.estValueRs)}</span>
  }
}

export default function History() {
  const userId = userFor('household')
  const res = useApi(() => api.scans(userId), [userId])
  if (res.loading && !res.data) return <Loading label="Loading your scans…" />
  if (res.error && !res.data) return <ErrorState error={res.error} onRetry={res.reload} />
  const scans = res.data?.scans ?? []

  return (
    <div className="flex flex-col gap-4">
      <h1 className="text-3xl font-bold">Your scans</h1>
      {scans.length === 0 ? (
        <Empty icon="🗑️" title="No scans yet">
          <Link to="/household/snap" className="font-semibold text-leaf">Snap your first bin →</Link>
        </Empty>
      ) : (
        <ul className="grid gap-3 md:grid-cols-2">
          {scans.map((s) => (
            <li key={s.scanId}>
              <Link to={`/household/result/${s.scanId}`} className="card flex items-center gap-4 hover:ring-2 hover:ring-leaf-200">
                <ScoreRing score={s.segregationScore} size={60} label="Score" />
                <div className="min-w-0 flex-1">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="font-semibold">{dateTime(s.createdAt)}</span>
                    <Status scan={s} />
                  </div>
                  <div className="mt-2">
                    <KgSplitBar totals={s.totals} showLegend={false} />
                  </div>
                </div>
              </Link>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
