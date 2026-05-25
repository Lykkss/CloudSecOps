export default function McPill({ value }) {
  if (!value) return <span className="mc-pill mc-pill-draft">—</span>
  const cls = `mc-pill mc-pill-${String(value).toLowerCase().replace(' ', '_')}`
  return <span className={cls}>{value}</span>
}

export function RolePill({ role }) {
  return <span className={`mc-pill mc-pill-${role}`}>{role}</span>
}

export function StatusPill({ active }) {
  return active
    ? <span className="mc-pill mc-pill-active">actif</span>
    : <span className="mc-pill mc-pill-inactive">inactif</span>
}

export function ScoreBadge({ score }) {
  if (score === null || score === undefined) return <span className="mc-score mc-score-orange">?</span>
  const cls = score < 40 ? 'mc-score-red' : score < 70 ? 'mc-score-orange' : 'mc-score-green'
  return <span className={`mc-score ${cls}`}>{score}/100</span>
}

export function RiskPill({ level }) {
  const label = level >= 12 ? 'Critique' : level >= 6 ? 'Élevé' : 'Faible'
  const cls   = level >= 12 ? 'mc-pill-critical' : level >= 6 ? 'mc-pill-high' : 'mc-pill-low'
  return <span className={`mc-pill ${cls}`}>{label}</span>
}
