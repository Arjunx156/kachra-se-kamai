/** "Demo" tag for demo-valued numbers (DEMO rates, simulated EPR, illustrative mountain). */
export function DemoBadge({ label = 'Demo', title }: { label?: string; title?: string }) {
  return (
    <span
      title={title ?? 'Demo value for the hackathon, not market data'}
      className="inline-flex items-center rounded-full border border-marigold-600/40 bg-marigold-50 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-marigold-700"
    >
      {label}
    </span>
  )
}

/** "AI estimate" tag for every number estimated by the vision model. */
export function AiBadge() {
  return (
    <span
      title="Estimated by AI from your photo. Final value is set at pickup."
      className="inline-flex items-center gap-1 rounded-full border border-leaf-200 bg-leaf-50 px-2 py-0.5 text-[11px] font-semibold uppercase tracking-wide text-leaf"
    >
      ✨ AI estimate
    </span>
  )
}
