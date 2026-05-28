'use client'

import { useEffect } from 'react'
import { X } from 'lucide-react'

interface ToastProps {
  message: string
  type?: 'success' | 'error'
  onDismiss: () => void
}

export function Toast({ message, type = 'success', onDismiss }: ToastProps) {
  useEffect(() => {
    const t = setTimeout(onDismiss, 4000)
    return () => clearTimeout(t)
  }, [onDismiss])

  return (
    <div className={`fixed top-4 right-4 z-50 flex items-center gap-3 px-4 py-3 rounded-lg shadow-lg text-sm font-medium animate-in slide-in-from-top-2 ${type === 'error' ? 'bg-error text-white' : 'bg-success text-white'}`}>
      <span>{message}</span>
      <button onClick={onDismiss} className="hover:opacity-75"><X size={14} /></button>
    </div>
  )
}
