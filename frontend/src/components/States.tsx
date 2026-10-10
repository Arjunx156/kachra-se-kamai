import type { ReactNode } from 'react'

export function Loading({ label = 'Loading…' }: { label?: string }) {
  return (
    <div role="status" className="flex items-center justify-center gap-3 py-12 text-slate/70">
      <span className="h-5 w-5 animate-spin rounded-full border-[3px] border-leaf-100 border-t-leaf" />
      <span>{label}</span>
    </div>
  )
}

export function ErrorState({ error, onRetry }: { error: Error; onRetry?: () => void }) {
  return (
    <div role="alert" className="card flex flex-col items-center gap-3 border-2 border-clay-50 text-center">
      <span className="text-3xl" aria-hidden>
        😕
      </span>
      <p className="max-w-sm text-slate">{error.message || 'Something went wrong.'}</p>
      {onRetry && (
        <button className="btn-ghost" onClick={onRetry}>
          Try again
        </button>
      )}
    </div>
  )
}

export function Empty({ icon, title, children }: { icon: string; title: string; children?: ReactNode }) {
  return (
    <div className="card flex flex-col items-center gap-2 py-10 text-center">
      <span className="text-4xl" aria-hidden>
        {icon}
      </span>
      <h3 className="text-xl font-semibold">{title}</h3>
      {children && <div className="max-w-sm text-slate/70">{children}</div>}
    </div>
  )
}
