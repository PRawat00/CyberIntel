/**
 * OAuth Callback Route Handler
 *
 * Handles OAuth redirects from Supabase (Google, GitHub, etc.)
 * This is a SERVER-SIDE route handler that exchanges the auth code
 * for a session BEFORE any client-side React code runs.
 *
 * This approach eliminates race conditions that occur with client-side
 * auth code exchange.
 */

import { createClient } from '@/lib/supabase/server'
import { NextResponse } from 'next/server'

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const next = searchParams.get('next') ?? '/dashboard'

  // Check for OAuth error from provider
  const error = searchParams.get('error')
  const errorDescription = searchParams.get('error_description')

  if (error) {
    console.error('OAuth error:', error, errorDescription)
    return NextResponse.redirect(
      `${origin}/auth/login?error=${encodeURIComponent(errorDescription || error)}`
    )
  }

  if (code) {
    const supabase = await createClient()
    const { error: exchangeError } = await supabase.auth.exchangeCodeForSession(code)

    if (!exchangeError) {
      // Handle different deployment environments
      const forwardedHost = request.headers.get('x-forwarded-host')
      const isLocalEnv = process.env.NODE_ENV === 'development'

      if (isLocalEnv) {
        // Local development - use origin directly
        return NextResponse.redirect(`${origin}${next}`)
      } else if (forwardedHost) {
        // Production with load balancer - use forwarded host
        return NextResponse.redirect(`https://${forwardedHost}${next}`)
      } else {
        // Production without load balancer
        return NextResponse.redirect(`${origin}${next}`)
      }
    }

    console.error('Code exchange error:', exchangeError)
  }

  // Return to login page with error if code exchange failed
  return NextResponse.redirect(`${origin}/auth/login?error=auth_callback_error`)
}
