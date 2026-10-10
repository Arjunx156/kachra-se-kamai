import { useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api, ApiError, uploadToS3 } from '../../api'
import { compressImage } from '../../lib/compressImage'
import { userFor } from '../../lib/role'

const STEPS = ['Uploading', 'AI is looking at your bin', 'Calculating your kamai'] as const
type Phase = 'idle' | 0 | 1 | 2 | 'error'

export default function Snap() {
  const userId = userFor('household')
  const navigate = useNavigate()
  const inputRef = useRef<HTMLInputElement>(null)
  const [file, setFile] = useState<File | null>(null)
  const [preview, setPreview] = useState<string | null>(null)
  const [phase, setPhase] = useState<Phase>('idle')
  const [error, setError] = useState<{ code: string; message: string } | null>(null)

  // The preview URL is handed to the Result page, so it is only revoked when replaced by a new photo.
  function choose(f: File | undefined) {
    if (!f) return
    if (preview) URL.revokeObjectURL(preview)
    setFile(f)
    setPreview(URL.createObjectURL(f))
    setPhase('idle')
    setError(null)
  }

  async function analyse() {
    if (!file) return
    setError(null)
    try {
      setPhase(0)
      const blob = await compressImage(file)
      const ticket = await api.createUpload(userId, 'image/jpeg')
      await uploadToS3(ticket.uploadUrl, blob, ticket.contentType)
      setPhase(1)
      const slowStep = window.setTimeout(() => setPhase(2), 4500)
      const scan = await api.createScan(userId, ticket.imageKey).finally(() => window.clearTimeout(slowStep))
      setPhase(2)
      navigate(`/household/result/${scan.scanId}`, { state: { scan, preview } })
    } catch (e) {
      setPhase('error')
      setError(e instanceof ApiError ? { code: e.code, message: e.message } : { code: 'ERROR', message: (e as Error).message })
    }
  }

  const busy = typeof phase === 'number'

  return (
    <div className="mx-auto flex max-w-md flex-col gap-4">
      <h1 className="text-3xl font-bold">Snap your bin</h1>
      <p className="-mt-2 text-slate/70">Take one clear photo from above. Our AI lists what's inside, what it's worth, and what's headed to landfill.</p>

      <input
        ref={inputRef}
        type="file"
        accept="image/*"
        capture="environment"
        className="sr-only"
        aria-label="Take or choose a bin photo"
        onChange={(e) => choose(e.target.files?.[0])}
      />

      {preview ? (
        <img src={preview} alt="Your bin photo" className="aspect-[4/3] w-full rounded-3xl object-cover shadow-card" />
      ) : (
        <button
          onClick={() => inputRef.current?.click()}
          className="flex aspect-[4/3] w-full flex-col items-center justify-center gap-3 rounded-3xl border-4 border-dashed border-leaf-200 bg-white text-leaf"
        >
          <span className="text-6xl" aria-hidden>📸</span>
          <span className="font-display text-xl font-bold">Tap to open camera</span>
        </button>
      )}

      {busy && (
        <ol className="card flex flex-col gap-3" aria-live="polite">
          {STEPS.map((s, i) => (
            <li key={s} className={`flex items-center gap-3 ${i > (phase as number) ? 'text-slate/40' : ''}`}>
              {i < (phase as number) ? (
                <span className="flex h-7 w-7 items-center justify-center rounded-full bg-leaf text-white">✓</span>
              ) : i === phase ? (
                <span className="h-7 w-7 animate-spin rounded-full border-[3px] border-leaf-100 border-t-leaf" />
              ) : (
                <span className="h-7 w-7 rounded-full border-[3px] border-cream-300" />
              )}
              <span className="font-display text-lg font-semibold">{s}{i === phase ? '…' : ''}</span>
            </li>
          ))}
        </ol>
      )}

      {error && (
        <div role="alert" className={`card border-2 ${error.code === 'NOT_A_BIN' ? 'border-marigold-100' : 'border-clay-50'}`}>
          <div className="text-2xl" aria-hidden>{error.code === 'NOT_A_BIN' ? '🤔' : '😕'}</div>
          <p className="mt-1">{error.message}</p>
        </div>
      )}

      {preview && !busy && (
        <div className="flex gap-3">
          <button className="btn-ghost flex-1" onClick={() => inputRef.current?.click()}>
            Retake
          </button>
          <button className="btn-primary flex-[2]" onClick={analyse}>
            {phase === 'error' ? 'Try again' : 'Check my bin'}
          </button>
        </div>
      )}
    </div>
  )
}
