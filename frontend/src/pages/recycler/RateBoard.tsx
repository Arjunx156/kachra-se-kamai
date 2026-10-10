import { useEffect, useState } from 'react'
import { api, ApiError } from '../../api'
import { DemoBadge } from '../../components/Badges'
import { MaterialChip } from '../../components/MaterialChip'
import { ErrorState, Loading } from '../../components/States'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'

const MAX_RATE = 500

export default function RateBoard() {
  const userId = userFor('recycler')
  const res = useApi(() => api.rates(), [])
  const [drafts, setDrafts] = useState<Record<string, string>>({})
  const [saving, setSaving] = useState<string | null>(null)
  const [saved, setSaved] = useState<string | null>(null)
  const [error, setError] = useState<Error | null>(null)

  useEffect(() => {
    if (res.data) setDrafts(Object.fromEntries(res.data.rates.map((r) => [r.material, String(r.rsPerKg)])))
  }, [res.data])

  async function save(material: string) {
    const value = Number(drafts[material])
    if (!Number.isFinite(value) || value < 0 || value > MAX_RATE) {
      setError(new Error(`Enter a rate between ₹0 and ₹${MAX_RATE} per kg.`))
      return
    }
    setSaving(material)
    setError(null)
    try {
      await api.setRate(material, value, userId)
      setSaved(material)
      window.setTimeout(() => setSaved((s) => (s === material ? null : s)), 2000)
      res.reload()
    } catch (e) {
      setError(e instanceof ApiError ? e : new Error('Could not save the rate.'))
    } finally {
      setSaving(null)
    }
  }

  if (res.loading && !res.data) return <Loading label="Loading rate board…" />
  if (res.error && !res.data) return <ErrorState error={res.error} onRetry={res.reload} />

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div className="flex flex-wrap items-center gap-3">
        <h1 className="text-3xl font-bold">Rate board</h1>
        <DemoBadge label="Demo rates" title="Seeded demo rates, not market data. Edit them to set your buy price." />
      </div>
      <p className="-mt-2 text-slate/70">Your ₹/kg buy rates drive every estimate and payout: households get 60%, pickers 40%.</p>
      {error && <ErrorState error={error} />}
      <ul className="card divide-y divide-cream-200 p-0">
        {res.data!.rates.map((r) => {
          const dirty = drafts[r.material] !== String(r.rsPerKg)
          return (
            <li key={r.material} className="flex items-center gap-3 px-4 py-3">
              <div className="min-w-0 flex-1">
                <MaterialChip code={r.material} />
                <div className="mt-0.5 text-xs text-slate/50">{r.isDemoRate ? 'Demo rate' : `Set by you`}</div>
              </div>
              <label className="flex items-center gap-1 rounded-xl border-2 border-cream-300 bg-cream px-2 focus-within:border-leaf">
                <span className="text-slate/60">₹</span>
                <input
                  type="number"
                  inputMode="decimal"
                  min={0}
                  max={MAX_RATE}
                  step={0.5}
                  aria-label={`${r.displayEn} rate in rupees per kg`}
                  value={drafts[r.material] ?? ''}
                  onChange={(e) => setDrafts((d) => ({ ...d, [r.material]: e.target.value }))}
                  className="num w-16 bg-transparent py-2 text-right text-lg outline-none"
                />
                <span className="text-sm text-slate/60">/kg</span>
              </label>
              <button className="btn-primary min-h-[44px] w-20 px-3 text-base" disabled={!dirty || saving === r.material} onClick={() => save(r.material)}>
                {saving === r.material ? '…' : saved === r.material ? '✓' : 'Save'}
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
