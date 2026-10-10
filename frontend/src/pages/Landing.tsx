import { useNavigate } from 'react-router-dom'
import { FACTS } from '../lib/facts'
import { DEMO_USERS, useRole } from '../lib/role'
import type { Role } from '../types'

const BENEFITS: { role: Role; who: string; gets: string }[] = [
  { role: 'household', who: 'Households', gets: 'Money for recyclables at posted rates, brand rewards, doorstep pickup with no haggling, and a daily score with tips.' },
  { role: 'picker', who: 'Waste pickers', gets: 'Pre-bundled pickups, a planned route, a guaranteed 40% share, and a visible earnings record.' },
  { role: 'recycler', who: 'Recyclers', gets: 'Steady, pre-sorted supply at the rates they set.' },
  { role: 'city', who: 'RWAs & the city', gets: 'Verified waste data, a society leaderboard, and a live landfill mountain.' },
]

const STEPS = [
  { icon: '📸', title: 'Snap your bin', body: 'Amazon Nova on Bedrock lists every item, estimates kg and spots brand packaging.' },
  { icon: '₹', title: 'See your kamai', body: 'Code (never the AI) prices recyclables from the recycler rate board.' },
  { icon: '🛺', title: 'Neighbours bundle up', body: 'Scans from your society become one pickup on a picker’s route.' },
  { icon: '⛰️', title: 'The mountain shrinks', body: 'Every kg collected is a kg kept off Delhi’s landfill.' },
]

export default function Landing() {
  const { setRole } = useRole()
  const navigate = useNavigate()
  const go = (r: Role) => {
    setRole(r)
    navigate(DEMO_USERS[r].home)
  }

  return (
    <div className="flex flex-col gap-10">
      <section className="relative overflow-hidden rounded-[2rem] bg-leaf px-6 py-10 text-white md:px-10 md:py-14">
        <div className="absolute -right-10 -top-10 h-56 w-56 rounded-full bg-marigold/20" aria-hidden />
        <div className="absolute -bottom-16 right-24 h-40 w-40 rounded-full bg-white/5" aria-hidden />
        <p className="font-display text-lg font-semibold text-marigold">कचरा से कमाई · earn from your waste</p>
        <h1 className="mt-2 max-w-2xl font-display text-4xl font-extrabold leading-[1.05] text-white md:text-6xl">
          Your dustbin is worth money. And Delhi's mountain can shrink.
        </h1>
        <p className="mt-4 max-w-xl text-lg text-white/85">
          Snap your bin. AI tells you what's in it, what it's worth, and what's headed to landfill. Your recyclables are bundled with your neighbours' and picked up by a local waste picker at a fair, transparent price.
        </p>
        <div className="mt-6 flex flex-wrap gap-3">
          <button className="btn-money text-xl" onClick={() => go('household')}>📸 Try it as a household</button>
          <button className="btn border-2 border-white/30 text-white hover:bg-white/10" onClick={() => go('city')}>See the city view</button>
        </div>
      </section>

      <section className="grid gap-3 md:grid-cols-3">
        <figure className="card md:col-span-2">
          <div className="num text-5xl text-clay">{FACTS.delhiWasteTpd.value.toLocaleString('en-IN')} t</div>
          <figcaption className="mt-1 text-slate/80">
            of waste a day in Delhi; only 7,611 t is processed.{' '}
            <a className="text-sm underline" href={FACTS.delhiWasteTpd.url} target="_blank" rel="noopener noreferrer">{FACTS.delhiWasteTpd.source}</a>
          </figcaption>
        </figure>
        <figure className="card">
          <div className="num text-5xl text-compost">{FACTS.ghazipurHeightM.value} m</div>
          <figcaption className="mt-1 text-slate/80">
            Ghazipur landfill (2018), vs Qutub Minar's {FACTS.qutubHeightM.value} m.{' '}
            <a className="text-sm underline" href={FACTS.ghazipurHeightM.url} target="_blank" rel="noopener noreferrer">Source</a>
          </figcaption>
        </figure>
      </section>

      <section>
        <h2 className="text-2xl font-bold">How it works</h2>
        <ol className="mt-3 grid gap-3 md:grid-cols-4">
          {STEPS.map((s, i) => (
            <li key={s.title} className="card relative">
              <span className="absolute right-4 top-3 font-display text-4xl font-extrabold text-cream-300">{i + 1}</span>
              <div className="text-3xl" aria-hidden>{s.icon}</div>
              <h3 className="mt-2 text-lg font-bold">{s.title}</h3>
              <p className="text-slate/70">{s.body}</p>
            </li>
          ))}
        </ol>
      </section>

      <section>
        <h2 className="text-2xl font-bold">Everyone gains something</h2>
        <p className="text-slate/70">Pick a role to explore the demo as that person.</p>
        <div className="mt-3 grid gap-3 md:grid-cols-2">
          {BENEFITS.map((b) => (
            <button key={b.role} onClick={() => go(b.role)} className="card flex items-start gap-4 text-left transition hover:-translate-y-0.5 hover:ring-2 hover:ring-leaf-200">
              <span className="text-4xl" aria-hidden>{DEMO_USERS[b.role].icon}</span>
              <span>
                <span className="block font-display text-xl font-bold">{b.who} →</span>
                <span className="text-slate/70">{b.gets}</span>
              </span>
            </button>
          ))}
          <div className="card border-2 border-dashed border-cream-300 bg-transparent shadow-none md:col-span-2">
            <span className="font-display text-lg font-bold">Brands (simulated)</span>{' '}
            <span className="text-slate/70">get verified, photo-backed collection of their plastic packaging for EPR take-back targets. No real brand integration in this demo.</span>
          </div>
        </div>
      </section>
    </div>
  )
}
