'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { authApi } from '@/lib/api'
import { LogOut } from 'lucide-react'

export function TopNav() {
  const { user, logout } = useAuth()
  const router = useRouter()
  const [open, setOpen] = useState(false)

  const initials = user?.email ? user.email.slice(0, 2).toUpperCase() : 'A'

  const handleLogout = async () => {
    try { await authApi.logout() } catch {}
    logout()
    router.push('/login')
  }

  return (
    <header className="h-14 border-b border-border bg-white flex items-center px-6 gap-4 shrink-0">
      <span className="flex items-center gap-2 font-semibold text-lg text-accent select-none">
        <svg width="20" height="20" viewBox="0 0 20 20" fill="none" className="text-accent">
          <circle cx="8" cy="8" r="5" stroke="currentColor" strokeWidth="2"/>
          <line x1="12" y1="12" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
        </svg>
        ReviewLens AI
      </span>

      <div className="flex-1" />

      <div className="relative">
        <button
          onClick={() => setOpen(o => !o)}
          className="w-8 h-8 rounded-full bg-accent text-white text-xs font-semibold flex items-center justify-center hover:bg-accent-hover focus:outline-none focus:ring-2 focus:ring-accent focus:ring-offset-2"
          aria-label="User menu"
        >
          {initials}
        </button>
        {open && (
          <div className="absolute right-0 mt-2 w-52 bg-white border border-border rounded-lg shadow-lg py-1 z-50">
            <div className="px-4 py-2 text-xs text-text-secondary border-b border-border truncate">{user?.email}</div>
            <button
              onClick={handleLogout}
              className="w-full flex items-center gap-2 px-4 py-2 text-sm text-text-primary hover:bg-raised transition-colors"
            >
              <LogOut size={14} />
              Sign out
            </button>
          </div>
        )}
      </div>
    </header>
  )
}
