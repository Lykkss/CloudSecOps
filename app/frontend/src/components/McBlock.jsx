import clsx from 'clsx'

export default function McBlock({ children, className, ...props }) {
  return (
    <div className={clsx('mc-block p-5 mb-4', className)} {...props}>
      {children}
    </div>
  )
}

export function McSectionTitle({ children, actions }) {
  return (
    <div className="flex items-center justify-between mb-4">
      <h2 className="mc-section-title mb-0">{children}</h2>
      {actions && <div className="flex gap-2">{actions}</div>}
    </div>
  )
}

export function McStat({ value, label, color = '#39D4E0', glow }) {
  return (
    <div className={clsx('mc-stat', glow && `shadow-${glow}`)}>
      <div className="val" style={{ color }}>{value}</div>
      <div className="lbl">{label}</div>
    </div>
  )
}

export function McSpinner() {
  return (
    <div className="flex items-center justify-center p-8">
      <div className="mc-spinner" />
      <span className="font-pixel text-mc-muted ml-3" style={{ fontSize: 9 }}>CHARGEMENT...</span>
    </div>
  )
}

export function McEmpty({ children = 'Aucune donnée' }) {
  return (
    <div className="text-center py-10 text-mc-muted font-pixel" style={{ fontSize: 9 }}>
      <div className="text-4xl mb-3">📦</div>
      {children}
    </div>
  )
}

export function McTorch() {
  return (
    <div className="flex items-center gap-2">
      <div style={{
        width: 6, height: 6,
        background: '#FEC84B',
        imageRendering: 'pixelated',
        animation: 'torch 0.15s steps(2) infinite',
      }} />
    </div>
  )
}
