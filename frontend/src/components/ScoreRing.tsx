export function scoreColor(score: number): string {
  if (score >= 70) return '#1F5F3F'
  if (score >= 40) return '#C98C00'
  return '#C2410C'
}

export function ScoreRing({ score, size = 96, label = 'Segregation' }: { score: number | null | undefined; size?: number; label?: string }) {
  const value = Math.max(0, Math.min(100, score ?? 0))
  const stroke = Math.round(size / 9)
  const r = (size - stroke) / 2
  const c = 2 * Math.PI * r
  const color = scoreColor(value)
  return (
    <div className="flex flex-col items-center" role="img" aria-label={`${label} score ${score ?? 'not available'} out of 100`}>
      <div className="relative" style={{ width: size, height: size }}>
        <svg width={size} height={size} className="-rotate-90">
          <circle cx={size / 2} cy={size / 2} r={r} stroke="#F1EBDD" strokeWidth={stroke} fill="none" />
          <circle
            cx={size / 2}
            cy={size / 2}
            r={r}
            stroke={color}
            strokeWidth={stroke}
            fill="none"
            strokeLinecap="round"
            strokeDasharray={c}
            strokeDashoffset={c * (1 - value / 100)}
            style={{ transition: 'stroke-dashoffset 800ms ease' }}
          />
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <span className="num" style={{ color, fontSize: size / 3.6 }}>
            {score ?? '–'}
          </span>
        </div>
      </div>
      <div className="label mt-1">{label}</div>
    </div>
  )
}
