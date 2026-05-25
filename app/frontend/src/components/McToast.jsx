import { useState, useCallback } from 'react'

let showToastFn = null

export function useToast() {
  const success = (msg) => showToastFn?.('success', msg)
  const error   = (msg) => showToastFn?.('error', msg)
  return { success, error }
}

export function ToastProvider() {
  const [toasts, setToasts] = useState([])

  showToastFn = (type, msg) => {
    const id = Date.now()
    setToasts(t => [...t, { id, type, msg }])
    setTimeout(() => setToasts(t => t.filter(x => x.id !== id)), 3500)
  }

  return (
    <div className="fixed bottom-5 right-5 z-50 flex flex-col gap-2">
      {toasts.map(t => (
        <div key={t.id} className={`mc-toast ${t.type === 'success' ? 'mc-toast-success' : 'mc-toast-error'}`}>
          {t.type === 'success' ? '✅ ' : '❌ '}{t.msg}
        </div>
      ))}
    </div>
  )
}
