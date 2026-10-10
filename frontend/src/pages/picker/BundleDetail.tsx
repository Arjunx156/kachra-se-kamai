import { useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { api, ApiError } from '../../api'
import { DemoBadge } from '../../components/Badges'
import { MaterialChip } from '../../components/MaterialChip'
import { ErrorState, Loading } from '../../components/States'
import { kg, rs } from '../../lib/format'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'
import type { Bundle } from '../../types'

export default function BundleDetail() {
  const { bundleId = '' } = useParams()
  const pickerId = userFor('picker')
  const res = useApi(() => api.bundle(bundleId), [bundleId])
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [done, setDone] = useState<Bundle | null>(null)
  const [error, setError] = useState<Error | null>(null)

  async function act(kind: 'accept' | 'collect') {
    setBusy(true)
    setError(null)
    try {
      const b = kind === 'accept' ? await api.accept(bundleId, pickerId) : await api.collect(bundleId, pickerId)
      if (kind === 'collect') setDone(b)
      setConfirming(false)
      res.reload()
    } catch (e) {
      setError(e instanceof ApiError ? e : new Error('Something went wrong.'))
    } finally {
      setBusy(false)
    }
  }

  if (res.loading && !res.data) return <Loading />
  if (res.error && !res.data) return <ErrorState error={res.error} onRetry={res.reload} />
  const b = res.data
  if (!b) return null

  if (done) {
    return (
      <div className="mx-auto flex max-w-md flex-col items-center gap-4 pt-6 text-center">
        <div className="text-7xl" aria-hidden>🎉</div>
        <h1 className="text-3xl font-bold">Collected!</h1>
        <div className="num text-6xl text-marigold-700">{rs(done.pickerRs)}</div>
        <p className="text-xl">added to your earnings</p>
        <div className="card w-full text-left">
          <div className="flex justify-between"><span>Bundle value</span><span className="num">{rs(done.valueRs)}</span></div>
          <div className="flex justify-between"><span>Your 40%</span><span className="num text-marigold-700">{rs(done.pickerRs)}</span></div>
          <div className="flex justify-between"><span>{done.householdCount} households, 60%</span><span className="num">{rs(done.householdRs)}</span></div>
          <div className="flex justify-between"><span>Brand rewards to households</span><span className="num">{rs(done.eprRs)}</span></div>
          <div className="mt-2"><DemoBadge label="Demo rates & split" /></div>
        </div>
        <Link to="/picker" className="btn-primary w-full">Next pickup →</Link>
      </div>
    )
  }

  const materials = Object.entries(b.materials).sort((a, z) => (z[1] ?? 0) - (a[1] ?? 0))
  const mineAccepted = b.status === 'accepted' && b.pickerId === pickerId

  return (
    <div className="mx-auto flex max-w-xl flex-col gap-4">
      <Link to="/picker" className="text-sm font-semibold text-leaf">← All pickups</Link>
      <div>
        <h1 className="text-3xl font-bold">{b.societyName}</h1>
        <p className="text-lg text-slate/70">{b.area}</p>
      </div>

      <section className="card grid grid-cols-3 gap-2 text-center">
        <div><div className="num text-4xl">{b.householdCount}</div><div className="label">homes</div></div>
        <div><div className="num text-4xl">{kg(b.totalKg)}</div><div className="label">total</div></div>
        <div><div className="num text-4xl text-marigold-700">{rs(b.pickerShareRs)}</div><div className="label">your share</div></div>
      </section>

      <section className="card">
        <h2 className="mb-2 text-xl font-bold">What to collect</h2>
        <ul className="divide-y divide-cream-200">
          {materials.map(([code, w]) => (
            <li key={code} className="flex items-center justify-between py-2">
              <MaterialChip code={code} />
              <span className="num text-xl">{kg(w)}</span>
            </li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-slate/60">Weights are AI estimates from household photos.</p>
      </section>

      {error && <ErrorState error={error} />}

      {b.status === 'open' && (
        <button className="btn-primary min-h-[64px] text-2xl" disabled={busy} onClick={() => act('accept')}>
          {busy ? 'Accepting…' : '✋ Accept pickup'}
        </button>
      )}
      {mineAccepted && (
        <button className="btn-money min-h-[64px] text-2xl" onClick={() => setConfirming(true)}>
          ✅ Mark collected
        </button>
      )}
      {b.status === 'accepted' && !mineAccepted && <p className="card text-center">Another picker has this pickup.</p>}
      {b.status === 'collected' && <p className="card text-center font-semibold text-leaf">✓ Collected · you earned {rs(b.pickerRs)}</p>}

      {confirming && (
        <div className="fixed inset-0 z-[2000] flex items-end justify-center bg-slate/50 p-4 sm:items-center" role="dialog" aria-modal="true" aria-labelledby="confirm-title">
          <div className="card w-full max-w-md">
            <h2 id="confirm-title" className="text-2xl font-bold">Collected everything from {b.societyName}?</h2>
            <p className="mt-2 text-slate/70">Households and you will be paid at today's rates.</p>
            <div className="mt-4 flex gap-3">
              <button className="btn-ghost flex-1" onClick={() => setConfirming(false)} disabled={busy}>Not yet</button>
              <button className="btn-money flex-[2]" onClick={() => act('collect')} disabled={busy}>
                {busy ? 'Saving…' : 'Yes, collected'}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
