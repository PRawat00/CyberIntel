/**
 * Next.js 16 Proxy Function
 *
 * Handles Supabase session refresh and route protection.
 * Uses official Supabase SSR pattern with getAll/setAll cookies.
 *
 * CRITICAL: Use getUser() not getSession() - only getUser() refreshes tokens
 */

import { createServerClient } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/upload', '/auth/profile']

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl
  let supabaseResponse = NextResponse.next({ request })

  const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
  const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

  // Supabase session refresh (production) - official pattern
  if (supabaseUrl && supabaseAnonKey) {
    const supabase = createServerClient(supabaseUrl, supabaseAnonKey, {
      cookies: {
        getAll() {
          return request.cookies.getAll()
        },
        setAll(cookiesToSet) {
          cookiesToSet.forEach(({ name, value }) => request.cookies.set(name, value))
          supabaseResponse = NextResponse.next({ request })
          cookiesToSet.forEach(({ name, value, options }) =>
            supabaseResponse.cookies.set(name, value, options)
          )
        },
      },
    })

    // CRITICAL: Use getUser() not getSession() - getUser() refreshes tokens
    // Don't put ANY code between createServerClient and getUser()
    const {
      data: { user },
    } = await supabase.auth.getUser()

    // Check protected routes with Supabase auth
    const isProtectedRoute = protectedRoutes.some((route) =>
      pathname.startsWith(route)
    )
    if (isProtectedRoute && !user) {
      const loginUrl = new URL('/auth/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      return NextResponse.redirect(loginUrl)
    }

    return supabaseResponse
  }

  // Fallback: Mock auth for localhost/development (when Supabase not configured)
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  // Allow public routes to pass through
  if (!isProtectedRoute) {
    return supabaseResponse
  }

  // Read session from cookie (mock auth)
  const sessionCookie = request.cookies.get('mock-auth-session')

  if (!sessionCookie) {
    // No session cookie, redirect to login
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  try {
    // Parse and validate session
    const session = JSON.parse(sessionCookie.value)

    // Check if session has expired
    if (new Date(session.expires_at) < new Date()) {
      // Session expired, redirect to login and clear cookie
      const loginUrl = new URL('/auth/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      const response = NextResponse.redirect(loginUrl)
      response.cookies.delete('mock-auth-session')
      return response
    }

    // Session is valid, allow access
    return supabaseResponse
  } catch {
    // Invalid session cookie, redirect to login and clear cookie
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    const response = NextResponse.redirect(loginUrl)
    response.cookies.delete('mock-auth-session')
    return response
  }
}

export const config = {
  matcher: [
    /*
     * Match all request paths except for the ones starting with:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public files (images, etc)
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.(?:svg|png|jpg|jpeg|gif|webp)$).*)',
  ],
}
