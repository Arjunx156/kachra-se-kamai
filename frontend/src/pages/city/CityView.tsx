import { Suspense, lazy, useEffect, useRef, useState } from 'react'
import { api } from '../../api'
import { DemoBadge } from '../../components/Badges'
import { ErrorState, Loading } from '../../components/States'
import { FACTS } from '../../lib/facts'
import { kg, rs } from '../../lib/format'
import { useApi } from '../../lib/useApi'

const Mountain3D = lazy(() => import('../../components/Mountain3D'))
const POLL_MS = 5000

function Counter({ label, value, tone = 'text-slate', badge }: { label: string; value: string; tone?: string; badge?: string }) {
  return (
    <div className="card p-4">
      <div className="label flex items-center gap-1.5">
        {label} {badge && <DemoBadge label={badge} />}
      </div>
      <div className={`num mt-1 text-3xl ${tone}`}>{value}</div>
    </div>
  )
}

export default function CityView() {
  const city = useApi(() => api.city(), [], POLL_MS)
  const board = useApi(() => api.leaderboard(), [], POLL_MS)
  const [flash, setFlash] = useState<string | null>(null)
  const lastDiverted = useRef<number | null>(null)

  // Announce when a collection diverts more kg (the mountain animates down at the same time).
  useEffect(() => {
    const v = city.data?.counters.divertedKg
    if (v === undefined) return
    if (lastDiverted.current !== null && v > lastDiverted.current) {
      setFlash(`−${kg(v - lastDiverted.current)} kept out of landfill`)
      const id = window.setTimeout(() => setFlash(null), 4000)
      lastDiverted.current = v
      return () => window.clearTimeout(id)
    }
    lastDiverted.current = v
  }, [city.data?.counters.divertedKg])

  if (city.loading && !city.data) return <Loading label="Loading the city view…" />
  if (city.error && !city.data) return <ErrorState error={city.error} onRetry={city.reload} />
  const c = city.data!.counters
  const m = city.data!.mountain

  return (
    <div className="flex flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold md:text-4xl">Delhi's waste, live</h1>
        <p className="text-slate/70">{FACTS.delhiWasteTpd.text}. <a className="underline" href={FACTS.delhiWasteTpd.url} target="_blank" rel="noopener noreferrer">{FACTS.delhiWasteTpd.source}</a></p>
      </div>

      <section className="relative">
        <Suspense fallback={<div className="h-[380px] rounded-3xl bg-cream-200 md:h-[460px]" />}>
          <Mountain3D heightFactor={m.heightFactor} className="h-[380px] bg-cream-200 md:h-[460px]" />
        </Suspense>
        <div className="pointer-events-none absolute left-4 top-4 rounded-2xl bg-white/90 p-3 shadow-card">
          <div className="label">Mountain height</div>
          <div className="num text-3xl text-clay">{Math.round(m.heightFactor * 100)}%</div>
          <div className="text-xs text-slate/60">{kg(m.divertedKg)} of {kg(m.targetKg)} demo target</div>
        </div>
        {flash && (
          <div role="status" className="absolute right-4 top-4 animate-bounce rounded-2xl bg-leaf px-4 py-2 font-display text-lg font-bold text-white shadow-card">
            {flash}
          </div>
        )}
        <p className="mt-2 text-sm text-slate/70">
          <strong>Illustrative: the mountain shrinks as Delhi diverts waste on this platform.</strong> It starts at Ghazipur's reported height ({FACTS.ghazipurHeightM.value} m,{' '}
          <a className="underline" href={FACTS.ghazipurHeightM.url} target="_blank" rel="noopener noreferrer">{FACTS.ghazipurHeightM.source}</a>) beside Qutub Minar ({FACTS.qutubHeightM.value} m,{' '}
          <a className="underline" href={FACTS.qutubHeightM.url} target="_blank" rel="noopener noreferrer">UNESCO</a>). It is not a physical measurement. <DemoBadge label="Demo target" />
        </p>
      </section>

      <section className="grid grid-cols-2 gap-3 md:grid-cols-5" aria-live="polite">
        <Counter label="Scanned" value={kg(c.scannedKg)} />
        <Counter label="Diverted" value={kg(c.divertedKg)} tone="text-leaf" />
        <Counter label="Paid to homes" value={rs(c.householdPayoutRs)} tone="text-marigold-700" badge="Demo" />
        <Counter label="Paid to pickers" value={rs(c.pickerPayoutRs)} tone="text-marigold-700" badge="Demo" />
        <Counter label="Brand rewards" value={rs(c.eprRs)} tone="text-marigold-700" badge="Sim." />
      </section>

      <section className="card p-0">
        <h2 className="px-5 pt-4 text-xl font-bold">Society leaderboard</h2>
        {board.error && !board.data ? (
          <div className="p-4"><ErrorState error={board.error} onRetry={board.reload} /></div>
        ) : (
          <div className="overflow-x-auto">
            <table className="mt-2 w-full text-left">
              <thead className="text-xs uppercase tracking-wider text-slate/60">
                <tr>
                  <th className="px-5 py-2">#</th>
                  <th className="py-2">Society</th>
                  <th className="py-2 text-right">Diverted</th>
                  <th className="px-5 py-2 text-right">Earned</th>
                </tr>
              </thead>
              <tbody>
                {(board.data?.societies ?? []).map((s) => (
                  <tr key={s.societyId} className="border-t border-cream-200">
                    <td className="num px-5 py-3 text-xl">{s.rank === 1 ? '🏆' : s.rank}</td>
                    <td className="py-3">
                      <div className="font-semibold">{s.name}</div>
                      <div className="text-sm text-slate/60">{s.area}</div>
                    </td>
                    <td className="num py-3 text-right text-leaf">{kg(s.divertedKg)}</td>
                    <td className="num px-5 py-3 text-right text-marigold-700">{rs(s.householdPayoutRs + s.eprRs)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <p className="text-xs text-slate/50">Society names are fictional; neighbourhoods are real Delhi areas. Updates every 5 seconds.</p>
    </div>
  )
}
