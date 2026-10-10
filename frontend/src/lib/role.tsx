import { createContext, useCallback, useContext, useMemo, useState, type ReactNode } from 'react'
import type { Role } from '../types'

/** Seeded demo users, one per role (created by POST /admin/seed). */
export const DEMO_USERS: Record<Role, { userId: string; name: string; label: string; home: string; icon: string }> = {
  household: { userId: 'u_priya', name: 'Priya', label: 'Household', home: '/household', icon: '🏠' },
  picker: { userId: 'u_ramesh', name: 'Ramesh', label: 'Picker', home: '/picker', icon: '🛺' },
  recycler: { userId: 'u_recycler', name: 'Green Loop', label: 'Recycler', home: '/recycler', icon: '♻️' },
  city: { userId: 'u_city', name: 'City', label: 'City', home: '/city', icon: '🏙️' },
}

const STORAGE_KEY = 'kachra.role'
const ROLES = Object.keys(DEMO_USERS) as Role[]

function readRole(): Role {
  try {
    const v = window.localStorage.getItem(STORAGE_KEY)
    return ROLES.includes(v as Role) ? (v as Role) : 'household'
  } catch {
    return 'household'
  }
}

interface RoleState {
  role: Role
  userId: string
  setRole: (r: Role) => void
}

const RoleContext = createContext<RoleState | null>(null)

export function RoleProvider({ children }: { children: ReactNode }) {
  const [role, setRoleState] = useState<Role>(readRole)
  const setRole = useCallback((r: Role) => {
    setRoleState(r)
    try {
      window.localStorage.setItem(STORAGE_KEY, r)
    } catch {
      /* storage unavailable (private mode): role still works for this session */
    }
  }, [])
  const value = useMemo(() => ({ role, userId: DEMO_USERS[role].userId, setRole }), [role, setRole])
  return <RoleContext.Provider value={value}>{children}</RoleContext.Provider>
}

export function useRole(): RoleState {
  const ctx = useContext(RoleContext)
  if (!ctx) throw new Error('useRole must be used inside RoleProvider')
  return ctx
}

export function userFor(role: Role): string {
  return DEMO_USERS[role].userId
}
