/**
 * OAuth Callback Page
 *
 * Handles OAuth redirects from Supabase (Google, GitHub, etc.)
 *
 * IMPORTANT: This page does NOT manually exchange the auth code.
 * Supabase's detectSessionInUrl (enabled in supabase.ts) automatically
 * detects and processes the OAuth code when the page loads.
 *
 * This page simply waits for the auth context to update and then redirects.
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/use-auth'

export default function AuthCallbackPage() {
  const router = useRouter()
  const { user, loading } = useAuth()
  const [error, setError] = useState<string | null>(null)
  const [hasCheckedUrl, setHasCheckedUrl] = useState(false)

  useEffect(() => {
    // Check for error in URL (only once)
    if (!hasCheckedUrl) {
      const searchParams = new URLSearchParams(window.location.search)
      const errorCode = searchParams.get('error')
      const errorDescription = searchParams.get('error_description')

      if (errorCode) {
        setError(errorDescription || 'Authentication failed')
      }
      setHasCheckedUrl(true)
    }
  }, [hasCheckedUrl])

  useEffect(() => {
    // Don't do anything if there's an error or still loading
    if (error || loading) return

    // Auth has finished loading
    if (user) {
      // Success - redirect to loading page for buffer
      // The loading page provides a 3-second delay to ensure auth state is fully settled
      router.replace('/auth/loading?redirect=/dashboard')
    } else {
      // No user after loading completed - this might happen if:
      // 1. The code was invalid/expired
      // 2. The user cancelled the OAuth flow
      // 3. There was a network issue
      // Give it a moment in case auth state is still propagating
      const timeout = setTimeout(() => {
        // Still no user, show error
        setError('Authentication failed. Please try again.')
      }, 2000) // 2 second grace period

      return () => clearTimeout(timeout)
    }
  }, [loading, user, router, error])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="mx-auto max-w-md rounded-lg border border-destructive bg-destructive/10 p-8 text-center">
          <div className="mb-4 text-4xl">!</div>
          <h1 className="mb-2 text-xl font-semibold text-destructive">Authentication Failed</h1>
          <p className="mb-4 text-sm text-muted-foreground">{error}</p>
          <button
            onClick={() => router.push('/auth/login')}
            className="rounded-md bg-primary px-4 py-2 text-sm font-medium text-primary-foreground hover:bg-primary/90"
          >
            Back to Login
          </button>
        </div>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen items-center justify-center bg-background">
      <div className="text-center">
        <div className="mb-4 inline-block h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
        <p className="text-sm text-muted-foreground">Completing sign in...</p>
      </div>
    </div>
  )
}
