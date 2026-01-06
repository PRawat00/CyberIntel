"use client"

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'
import { logger } from '@/lib/logger'
import CounterLoader from '@/components/ui/counter-loader'

interface AuthLoadingWrapperProps {
  children: React.ReactNode
}

/**
 * Wrapper component for protected pages that handles auth loading states
 * Shows the counter loader animation while checking authentication
 * Redirects to login if user is not authenticated
 */
export function AuthLoadingWrapper({ children }: AuthLoadingWrapperProps) {
  const { user, loading } = useAuth()
  const router = useRouter()
  const [isRedirecting, setIsRedirecting] = useState(false)

  useEffect(() => {
    // Only redirect after loading is complete and there's no user
    // Add a small debounce to prevent premature redirects during auth initialization
    if (!loading && !user && !isRedirecting) {
      logger.log('[AUTH WRAPPER] No user found after loading complete, redirecting to login...')
      setIsRedirecting(true)

      // Small delay to give auth state one final chance to settle
      const timeout = setTimeout(() => {
        router.push('/auth/login')
      }, 100)

      return () => clearTimeout(timeout)
    }
  }, [loading, user, router, isRedirecting])

  // Show loading animation while auth state is initializing
  if (loading) {
    return <CounterLoader />
  }

  // Show loading animation while redirecting to login
  if (!user) {
    return <CounterLoader />
  }

  // User is authenticated, show the protected content
  return <>{children}</>
}
