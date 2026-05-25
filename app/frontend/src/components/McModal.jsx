export default function McModal({ open, onClose, title, children }) {
  if (!open) return null
  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center"
      style={{ background: 'rgba(0,0,0,0.85)' }}
      onClick={(e) => e.target === e.currentTarget && onClose()}
    >
      <div className="mc-block w-full max-w-lg max-h-[90vh] overflow-y-auto" style={{ position: 'relative', zIndex: 51 }}>
        <div className="flex items-center justify-between mb-5">
          <span className="font-pixel text-mc-diamond" style={{ fontSize: 11 }}>{title}</span>
          <button
            onClick={onClose}
            className="mc-btn mc-btn-ghost mc-btn-sm"
            style={{ lineHeight: 1 }}
          >✕</button>
        </div>
        {children}
      </div>
    </div>
  )
}

export function McField({ label, children }) {
  return (
    <div className="mb-4">
      <label className="block font-pixel text-mc-muted mb-2" style={{ fontSize: 8 }}>{label}</label>
      {children}
    </div>
  )
}
