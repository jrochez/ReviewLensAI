'use client'

import { Suspense, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'
import { authApi } from '@/lib/api'

function LoginForm() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const res = await authApi.login(email, password)
      login('', res.user)
      const next = searchParams.get('next')
      router.push(next && next.startsWith('/') ? next : '/datasets')
    } catch (err: any) {
      setError(err?.data?.message || 'Invalid email or password.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-surface px-4">
      <div className="w-full max-w-sm">
        <div className="bg-white border border-border rounded-xl shadow-sm p-8">
          <div className="flex items-center gap-2 justify-center mb-6">
            <svg width="24" height="24" viewBox="0 0 20 20" fill="none" className="text-accent">
              <circle cx="8" cy="8" r="5" stroke="currentColor" strokeWidth="2"/>
              <line x1="12" y1="12" x2="18" y2="18" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
            <span className="text-xl font-semibold text-accent">ReviewLens AI</span>
          </div>

          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <label className="block text-sm font-medium text-text-primary mb-1" htmlFor="email">Email</label>
              <input
                id="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={e => setEmail(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
                placeholder="analyst@firm.com"
              />
            </div>

            <div>
              <label className="block text-sm font-medium text-text-primary mb-1" htmlFor="password">Password</label>
              <input
                id="password"
                type="password"
                autoComplete="current-password"
                required
                value={password}
                onChange={e => setPassword(e.target.value)}
                className="w-full px-3 py-2 border border-border rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-accent focus:border-transparent"
              />
            </div>

            {error && (
              <p role="alert" className="text-error text-sm">{error}</p>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-accent hover:bg-accent-hover text-white font-medium py-2 px-4 rounded-lg text-sm transition-colors disabled:opacity-60"
            >
              {loading ? 'Signing in…' : 'Sign In'}
            </button>
          </form>
        </div>

        <p className="text-center text-xs text-text-secondary mt-6">© ReviewLens AI 2026</p>
      </div>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense>
      <LoginForm />
    </Suspense>
  )
}
