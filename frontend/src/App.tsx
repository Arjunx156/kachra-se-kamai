import { lazy, Suspense, useEffect } from 'react'
import { Link, Navigate, NavLink, Route, Routes, useLocation, useNavigate } from 'react-router-dom'
import { Loading } from './components/States'
import { DEMO_USERS, useRole } from './lib/role'
import Landing from './pages/Landing'
import HouseholdCoach from './pages/household/Coach'
import HouseholdHistory from './pages/household/History'
import HouseholdHome from './pages/household/Home'
import HouseholdResult from './pages/household/Result'
import HouseholdSnap from './pages/household/Snap'
import PickerBundleDetail from './pages/picker/BundleDetail'
import PickerEarnings from './pages/picker/Earnings'
import RecyclerIncoming from './pages/recycler/Incoming'
import RecyclerRateBoard from './pages/recycler/RateBoard'
import type { Role } from './types'

// Heavy pages (three.js, Leaflet) are code-split.
const CityView = lazy(() => import('./pages/city/CityView'))
const PickerBundles = lazy(() => import('./pages/picker/Bundles'))

const ROLES = Object.keys(DEMO_USERS) as Role[]

const TABS: Record<Role, { to: string; label: string; end?: boolean }[]> = {
  household: [
    { to: '/household', label: 'Home', end: true },
    { to: '/household/snap', label: '📸 Snap' },
    { to: '/household/history', label: 'History' },
    { to: '/household/coach', label: 'Coach' },
  ],
  picker: [
    { to: '/picker', label: 'Pickups', end: true },
    { to: '/picker/earnings', label: 'Earnings' },
  ],
  recycler: [
    { to: '/recycler', label: 'Rate board', end: true },
    { to: '/recycler/incoming', label: 'Incoming' },
  ],
  city: [{ to: '/city', label: 'City view', end: true }],
}

function roleFromPath(path: string): Role | null {
  const seg = path.split('/')[1]
  return ROLES.includes(seg as Role) ? (seg as Role) : null
}

function TopBar() {
  const { role, setRole } = useRole()
  const navigate = useNavigate()
  const { pathname } = useLocation()
  const pathRole = roleFromPath(pathname)

  // Deep links (e.g. /picker/earnings) select the matching demo user.
  useEffect(() => {
    if (pathRole && pathRole !== role) setRole(pathRole)
  }, [pathRole, role, setRole])

  const active = pathRole ?? role
  return (
    <header className="sticky top-0 z-[1000] border-b border-cream-300 bg-cream/95 backdrop-blur">
      <div className="mx-auto flex max-w-5xl items-center gap-3 px-4 pt-3">
        <Link to="/" className="font-display text-xl font-extrabold leading-none text-leaf">
          Kachra se <span className="text-marigold-600">Kamai</span>
        </Link>
        <span className="ml-auto hidden text-sm text-slate/60 sm:inline">Viewing as {DEMO_USERS[active].name}</span>
      </div>
      <nav aria-label="Choose a role" className="mx-auto max-w-5xl px-4 py-2">
        <div className="grid grid-cols-4 gap-1 rounded-2xl bg-cream-200 p-1">
          {ROLES.map((r) => (
            <button
              key={r}
              aria-pressed={pathRole === r}
              onClick={() => {
                setRole(r)
                navigate(DEMO_USERS[r].home)
              }}
              className={`flex min-h-[44px] flex-col items-center justify-center rounded-xl px-1 text-xs font-semibold transition sm:flex-row sm:gap-1.5 sm:text-sm ${
                pathRole === r ? 'bg-white text-leaf shadow-card' : 'text-slate/70 hover:text-slate'
              }`}
            >
              <span aria-hidden>{DEMO_USERS[r].icon}</span>
              {DEMO_USERS[r].label}
            </button>
          ))}
        </div>
      </nav>
      {pathRole && TABS[pathRole].length > 1 && (
        <nav aria-label="Sections" className="mx-auto flex max-w-5xl gap-1 overflow-x-auto px-4 pb-2">
          {TABS[pathRole].map((t) => (
            <NavLink
              key={t.to}
              to={t.to}
              end={t.end}
              className={({ isActive }) =>
                `whitespace-nowrap rounded-full px-4 py-1.5 text-sm font-semibold ${isActive ? 'bg-leaf text-white' : 'text-slate/70 hover:bg-cream-200'}`
              }
            >
              {t.label}
            </NavLink>
          ))}
        </nav>
      )}
    </header>
  )
}

export default function App() {
  return (
    <div className="min-h-screen pb-16">
      <TopBar />
      <main className="mx-auto max-w-5xl px-4 pt-4">
        <Suspense fallback={<Loading />}>
          <Routes>
            <Route path="/" element={<Landing />} />
            <Route path="/household" element={<HouseholdHome />} />
            <Route path="/household/snap" element={<HouseholdSnap />} />
            <Route path="/household/result/:scanId" element={<HouseholdResult />} />
            <Route path="/household/history" element={<HouseholdHistory />} />
            <Route path="/household/coach" element={<HouseholdCoach />} />
            <Route path="/picker" element={<PickerBundles />} />
            <Route path="/picker/bundle/:bundleId" element={<PickerBundleDetail />} />
            <Route path="/picker/earnings" element={<PickerEarnings />} />
            <Route path="/recycler" element={<RecyclerRateBoard />} />
            <Route path="/recycler/incoming" element={<RecyclerIncoming />} />
            <Route path="/city" element={<CityView />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </Suspense>
      </main>
      <footer className="mx-auto mt-12 max-w-5xl px-4 text-center text-xs text-slate/50">
        Hackathon demo · Rates, payouts and brand rewards are demo values · AI weights are estimates
      </footer>
    </div>
  )
}
