import { kg, rs } from '../lib/format'
import type { Me } from '../types'
import { DemoBadge } from './Badges'

export function WalletCard({ me }: { me: Me }) {
  const w = me.wallet
  return (
    <section className="card overflow-hidden bg-leaf p-0 text-white" aria-label="Your wallet">
      <div className="p-5">
        <div className="text-sm font-semibold uppercase tracking-wider text-white/70">Your kamai</div>
        <div className="num mt-1 text-5xl text-marigold">{rs(w.householdPayoutRs + w.eprRs)}</div>
        <div className="mt-1 text-white/80">
          {rs(w.householdPayoutRs)} from recyclables · {rs(w.eprRs)} brand rewards <DemoBadge label="Simulated EPR" />
        </div>
        {(me.pendingRs ?? 0) > 0 && (
          <div className="mt-2 text-sm text-white/80">+ about {rs(me.pendingRs)} waiting in your next pickup (AI estimate)</div>
        )}
      </div>
      <div className="grid grid-cols-2 divide-x divide-white/15 border-t border-white/15 bg-leaf-700">
        <div className="p-4">
          <div className="text-xs uppercase tracking-wider text-white/60">Kept out of landfill</div>
          <div className="num text-2xl">{kg(w.divertedKg)}</div>
        </div>
        <div className="p-4">
          <div className="text-xs uppercase tracking-wider text-white/60">To landfill this week</div>
          <div className="num text-2xl text-[#FDBA8C]">{kg(me.week?.landfillKg)}</div>
        </div>
      </div>
    </section>
  )
}
