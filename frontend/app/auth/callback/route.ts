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

// Whitelist of allowed redirect paths (prevents open redirect vulnerability)
const ALLOWED_REDIRECTS = [
  '/dashboard',
  '/dashboard/scans',
  '/dashboard/integrations',
  '/auth/profile',
  '/',
]

/**
 * Validate that the redirect URL is safe (same-origin and whitelisted)
 */
function isValidRedirect(next: string): boolean {
  // Must start with / (relative URL)
  if (!next.startsWith('/')) return false
  // Must not be a protocol-relative URL (//evil.com)
  if (next.startsWith('//')) return false
  // Check against whitelist
  return ALLOWED_REDIRECTS.some(allowed =>
    next === allowed || next.startsWith(allowed + '/')
  )
}

export async function GET(request: Request) {
  const { searchParams, origin } = new URL(request.url)
  const code = searchParams.get('code')
  const nextParam = searchParams.get('next') ?? '/dashboard'

  // Validate redirect URL to prevent open redirect attacks
  const next = isValidRedirect(nextParam) ? nextParam : '/dashboard'

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
