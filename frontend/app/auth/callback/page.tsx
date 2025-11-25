/**
 * OAuth Callback Page
 *
 * Handles OAuth redirects from Supabase (Google, GitHub, etc.)
 * Exchanges the auth code for a session and redirects to dashboard
 */

'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { supabase } from '@/lib/supabase'

export default function AuthCallbackPage() {
  const router = useRouter()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    // Handle the OAuth callback
    const handleCallback = async () => {
      try {
        // Check if Supabase is configured
        if (!supabase) {
          setError('Authentication service not configured')
          return
        }

        // Get the code from the URL
        const hashParams = new URLSearchParams(window.location.hash.substring(1))
        const searchParams = new URLSearchParams(window.location.search)

        const code = searchParams.get('code')
        const errorCode = searchParams.get('error')
        const errorDescription = searchParams.get('error_description')

        if (errorCode) {
          setError(errorDescription || 'Authentication failed')
          return
        }

        if (!code) {
          // If no code, check for hash-based tokens (older OAuth flow)
          const accessToken = hashParams.get('access_token')
          if (accessToken) {
            // Session already set by Supabase client
            // Use loading page to give auth context time to initialize
            router.replace('/auth/loading?redirect=/dashboard')
            return
          }

          setError('No authentication code received')
          return
        }

        // Exchange code for session
        const { data, error: sessionError } = await supabase.auth.exchangeCodeForSession(code)

        if (sessionError) {
          setError(sessionError.message)
          return
        }

        if (data.session) {
          // Success! Redirect through loading page to give auth context time to initialize
          router.replace('/auth/loading?redirect=/dashboard')
        } else {
          setError('Failed to create session')
        }
      } catch (err) {
        console.error('Callback error:', err)
        setError('An unexpected error occurred')
      }
    }

    handleCallback()
  }, [router])

  if (error) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-background">
        <div className="mx-auto max-w-md rounded-lg border border-destructive bg-destructive/10 p-8 text-center">
          <div className="mb-4 text-4xl">⚠️</div>
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
