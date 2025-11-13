"use client"

import { useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'
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

  useEffect(() => {
    // Only redirect after loading is complete and there's no user
    if (!loading && !user) {
      router.push('/auth/login')
    }
  }, [loading, user, router])

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
