'use client'

import { createContext, useContext, useEffect, useState, ReactNode } from 'react'
import { authApi } from '@/lib/api'
import { User } from '@/types'

interface AuthContextValue {
  token: string | null
  user: User | null
  login: (token: string, user: User) => void
  logout: () => void
  isAuthenticated: boolean
  initialized: boolean
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [initialized, setInitialized] = useState(false)

  useEffect(() => {
    // Restore session by validating the HttpOnly cookie with the server.
    // No user data is stored in client-side storage.
    authApi.me()
      .then(u => setUser(u as User))
      .catch(() => {})
      .finally(() => setInitialized(true))
  }, [])

  // token param kept for call-site compatibility; auth is via HttpOnly cookie.
  const login = (_token: string, newUser: User) => {
    setUser(newUser)
  }

  const logout = () => {
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ token: null, user, login, logout, isAuthenticated: !!user, initialized }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth() {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used within AuthProvider')
  return ctx
}
