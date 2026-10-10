import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError } from '../../api'
import { BundleCard } from '../../components/BundleCard'
import RouteMap from '../../components/RouteMap'
import { Empty, ErrorState, Loading } from '../../components/States'
import { rs } from '../../lib/format'
import { userFor } from '../../lib/role'
import { useApi } from '../../lib/useApi'
import type { Bundle } from '../../types'

export default function Bundles() {
  const pickerId = userFor('picker')
  const navigate = useNavigate()
  const open = useApi(() => api.bundles('open', pickerId), [pickerId])
  const mine = useApi(() => api.bundles('accepted', pickerId), [pickerId])
  const [busyId, setBusyId] = useState<string | null>(null)
  const [refreshing, setRefreshing] = useState(false)
  const [notice, setNotice] = useState<string | null>(null)
  const [actionError, setActionError] = useState<Error | null>(null)

  async function refresh() {
    setRefreshing(true)
    setActionError(null)
    try {
      const { created } = await api.buildBundles()
      setNotice(created > 0 ? `${created} new pickup${created > 1 ? 's' : ''} ready` : 'No new pickups yet')
      open.reload()
      mine.reload()
    } catch (e) {
      setActionError(e as Error)
    } finally {
      setRefreshing(false)
    }
  }

  async function accept(b: Bundle) {
    setBusyId(b.bundleId)
    setActionError(null)
    try {
      await api.accept(b.bundleId, pickerId)
      navigate(`/picker/bundle/${b.bundleId}`)
    } catch (e) {
      setActionError(e instanceof ApiError ? e : new Error('Could not accept this pickup.'))
      open.reload()
    } finally {
      setBusyId(null)
    }
  }

  const openList = open.data?.bundles ?? []
  const mineList = mine.data?.bundles ?? []
  const potential = openList.reduce((s, b) => s + b.pickerShareRs, 0)

  return (
    <div className="flex flex-col gap-4">
      <div className="flex items-center justify-between gap-3">
        <div>
          <h1 className="text-3xl font-bold">Today's pickups</h1>
          {open.data && (
            <p className="text-lg text-slate/70">
              {openList.length} stops · {open.data.totalRouteKm.toFixed(1)} km · up to <span className="num text-marigold-700">{rs(potential)}</span>
            </p>
          )}
        </div>
        <button className="btn-ghost shrink-0" onClick={refresh} disabled={refreshing}>
          {refreshing ? '…' : '🔄 Refresh'}
        </button>
      </div>
      {notice && <p className="rounded-2xl bg-leaf-50 p-3 font-semibold text-leaf" role="status">{notice}</p>}
      {actionError && <ErrorState error={actionError} />}

      {mineList.length > 0 && (
        <section className="flex flex-col gap-3">
          <h2 className="text-xl font-bold">Accepted by you</h2>
          {mineList.map((b) => (
            <BundleCard key={b.bundleId} bundle={b} />
          ))}
        </section>
      )}

      {open.loading && !open.data ? (
        <Loading label="Finding pickups near you…" />
      ) : open.error && !open.data ? (
        <ErrorState error={open.error} onRetry={open.reload} />
      ) : (
        <>
          <RouteMap bundles={[...openList, ...mineList]} base={open.data?.base ?? null} />
          {openList.length === 0 ? (
            <Empty icon="🛺" title="No open pickups">
              Tap Refresh to bundle the latest household scans.
            </Empty>
          ) : (
            <section className="grid gap-3 md:grid-cols-2">
              {openList.map((b) => (
                <BundleCard key={b.bundleId} bundle={b} onAccept={accept} busy={busyId === b.bundleId} />
              ))}
            </section>
          )}
        </>
      )}
    </div>
  )
}
