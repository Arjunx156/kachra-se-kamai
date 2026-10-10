import { useState } from 'react'
import { api, ApiError } from '../../api'
import { ErrorState } from '../../components/States'
import { userFor } from '../../lib/role'
import type { CoachPlan } from '../../types'

export default function Coach() {
  const userId = userFor('household')
  const [language, setLanguage] = useState<'en' | 'hi'>('en')
  const [plan, setPlan] = useState<CoachPlan | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<Error | null>(null)

  async function ask() {
    setLoading(true)
    setError(null)
    try {
      setPlan(await api.coach(userId, language))
    } catch (e) {
      setError(e instanceof ApiError ? e : new Error('The coach could not answer right now.'))
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="mx-auto flex max-w-2xl flex-col gap-4">
      <div>
        <h1 className="text-3xl font-bold">Kamai Coach</h1>
        <p className="text-slate/70">An AI agent that reads your real scan data and writes a 3-step plan for this week.</p>
      </div>

      <div className="flex items-center gap-3">
        <div role="radiogroup" aria-label="Language" className="grid grid-cols-2 gap-1 rounded-2xl bg-cream-200 p-1">
          {(['en', 'hi'] as const).map((l) => (
            <button
              key={l}
              role="radio"
              aria-checked={language === l}
              onClick={() => setLanguage(l)}
              className={`min-h-[44px] rounded-xl px-4 font-semibold ${language === l ? 'bg-white text-leaf shadow-card' : 'text-slate/70'}`}
            >
              {l === 'en' ? 'English' : 'Hinglish'}
            </button>
          ))}
        </div>
        <button className="btn-primary flex-1" onClick={ask} disabled={loading}>
          {loading ? 'Thinking…' : '🧭 Get my weekly plan'}
        </button>
      </div>

      {loading && (
        <div className="card animate-pulse text-slate/70" aria-live="polite">
          The coach is checking your last 7 days, your scans, today's rates and your society's rank…
        </div>
      )}
      {error && <ErrorState error={error} onRetry={ask} />}

      {plan && !loading && (
        <article className="card flex flex-col gap-3">
          {plan.checked.length > 0 && (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="font-semibold text-leaf">✓ Checked:</span>
              {plan.checked.map((c) => (
                <span key={c} className="rounded-full bg-leaf-50 px-3 py-1 font-semibold text-leaf">{c}</span>
              ))}
            </div>
          )}
          <div className="whitespace-pre-wrap text-lg leading-relaxed">{plan.plan}</div>
          <footer className="border-t border-cream-200 pt-2 text-xs text-slate/60">
            {plan.onboarding
              ? 'Snap a couple of bins first; then the coach can use your real data.'
              : `Written by a Strands agent on Amazon Bedrock using tools over your data (${plan.toolsCalled.join(', ')}). Rs figures use demo rates.`}
          </footer>
        </article>
      )}
    </div>
  )
}
