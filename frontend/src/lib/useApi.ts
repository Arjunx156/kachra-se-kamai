import { useCallback, useEffect, useRef, useState } from 'react'

export interface ApiState<T> {
  data: T | null
  error: Error | null
  loading: boolean
  reload: () => void
}

/** Run an async loader on mount / when deps change, optionally polling. Keeps last data while refreshing. */
export function useApi<T>(loader: () => Promise<T>, deps: unknown[], pollMs?: number): ApiState<T> {
  const [data, setData] = useState<T | null>(null)
  const [error, setError] = useState<Error | null>(null)
  const [loading, setLoading] = useState(true)
  const [tick, setTick] = useState(0)
  const loaderRef = useRef(loader)
  loaderRef.current = loader

  useEffect(() => {
    let alive = true
    setLoading(true)
    loaderRef
      .current()
      .then((d) => {
        if (!alive) return
        setData(d)
        setError(null)
      })
      .catch((e: unknown) => alive && setError(e instanceof Error ? e : new Error(String(e))))
      .finally(() => alive && setLoading(false))
    return () => {
      alive = false
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [...deps, tick])

  useEffect(() => {
    if (!pollMs) return
    const id = window.setInterval(() => setTick((t) => t + 1), pollMs)
    return () => window.clearInterval(id)
  }, [pollMs])

  const reload = useCallback(() => setTick((t) => t + 1), [])
  return { data, error, loading, reload }
}
