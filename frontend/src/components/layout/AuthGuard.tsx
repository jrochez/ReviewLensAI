'use client'

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/lib/auth-context'

export function AuthGuard({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, initialized } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (initialized && !isAuthenticated) router.replace('/login')
  }, [isAuthenticated, initialized, router])

  if (!initialized || !isAuthenticated) return null
  return <>{children}</>
}
