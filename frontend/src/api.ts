import type {
  Bundle,
  BundleList,
  BundleStatus,
  CityStats,
  CoachPlan,
  LeaderRow,
  Me,
  Rate,
  Scan,
  UploadTicket,
} from './types'

const BASE = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

export class ApiError extends Error {
  constructor(
    public code: string,
    message: string,
    public status: number,
  ) {
    super(message)
  }
}

type Envelope<T> = { ok: true; data: T } | { ok: false; error: { code: string; message: string } }

async function request<T>(method: string, path: string, body?: unknown): Promise<T> {
  if (!BASE) {
    throw new ApiError('NO_API_URL', 'The app is not connected to its API yet (VITE_API_URL is missing).', 0)
  }
  let res: Response
  try {
    res = await fetch(`${BASE}${path}`, {
      method,
      headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body),
    })
  } catch {
    throw new ApiError('NETWORK', "Can't reach the server. Check your connection and try again.", 0)
  }
  let payload: Envelope<T>
  try {
    payload = (await res.json()) as Envelope<T>
  } catch {
    throw new ApiError('BAD_RESPONSE', 'The server sent an unexpected reply. Please try again.', res.status)
  }
  if (!payload.ok) throw new ApiError(payload.error.code, payload.error.message, res.status)
  return payload.data
}

const q = (params: Record<string, string | undefined>) => {
  const s = new URLSearchParams()
  Object.entries(params).forEach(([k, v]) => v !== undefined && s.set(k, v))
  return `?${s.toString()}`
}

export const api = {
  me: (userId: string) => request<Me>('GET', `/me${q({ userId })}`),
  createUpload: (userId: string, contentType: string) => request<UploadTicket>('POST', '/uploads', { userId, contentType }),
  createScan: (userId: string, imageKey: string) => request<Scan>('POST', '/scans', { userId, imageKey }),
  scans: (userId: string) => request<{ scans: Scan[] }>('GET', `/scans${q({ userId })}`),
  scan: (userId: string, scanId: string) => request<Scan>('GET', `/scans/${encodeURIComponent(scanId)}${q({ userId })}`),
  rates: () => request<{ rates: Rate[]; note: string }>('GET', '/rates'),
  setRate: (material: string, rsPerKg: number, userId: string) =>
    request<Rate>('PUT', `/rates/${material}`, { rsPerKg, userId }),
  buildBundles: () => request<{ created: number }>('POST', '/bundles/build'),
  bundles: (status: BundleStatus, pickerId?: string) => request<BundleList>('GET', `/bundles${q({ status, pickerId })}`),
  bundle: (id: string) => request<Bundle>('GET', `/bundles/${encodeURIComponent(id)}`),
  accept: (id: string, pickerId: string) => request<Bundle>('POST', `/bundles/${encodeURIComponent(id)}/accept`, { pickerId }),
  collect: (id: string, pickerId: string) => request<Bundle>('POST', `/bundles/${encodeURIComponent(id)}/collect`, { pickerId }),
  city: () => request<CityStats>('GET', '/stats/city'),
  leaderboard: () => request<{ societies: LeaderRow[] }>('GET', '/leaderboard'),
  coach: (userId: string, language: 'en' | 'hi') => request<CoachPlan>('POST', '/coach', { userId, language }),
}

export async function uploadToS3(url: string, blob: Blob, contentType: string): Promise<void> {
  let res: Response
  try {
    res = await fetch(url, { method: 'PUT', headers: { 'Content-Type': contentType }, body: blob })
  } catch {
    throw new ApiError('UPLOAD_FAILED', 'Photo upload failed. Check your connection and try again.', 0)
  }
  if (!res.ok) throw new ApiError('UPLOAD_FAILED', 'Photo upload failed. Please try again.', res.status)
}
