/**
 * Next.js Proxy for Route Protection
 *
 * Protects routes that require authentication.
 * Redirects unauthenticated users to login page.
 *
 * Updated to follow Next.js 16 conventions:
 * - File named proxy.ts (middleware.ts is deprecated)
 * - Function exported as proxy
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/upload', '/auth/profile']

// Public routes (accessible without auth)
const publicRoutes = ['/', '/auth/login', '/auth/signup']

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Explicitly skip API routes - they go directly to backend
  // This ensures no interference with API calls
  if (pathname.startsWith('/api')) {
    return NextResponse.next()
  }

  // Check if route requires authentication
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  if (!isProtectedRoute) {
    return NextResponse.next()
  }

  // Check for auth session in cookies
  const sessionCookie = request.cookies.get('mock-auth-session')

  // For Supabase auth, we check for the sb-access-token cookie
  const supabaseToken = request.cookies.get('sb-access-token')

  // If no session cookie and no Supabase token, redirect to login
  if (!sessionCookie && !supabaseToken) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Verify session is valid (not expired) for mock auth
  if (sessionCookie) {
    try {
      const session = JSON.parse(sessionCookie.value)
      const expiresAt = new Date(session.expires_at)

      if (expiresAt < new Date()) {
        // Session expired, redirect to login
        const loginUrl = new URL('/auth/login', request.url)
        loginUrl.searchParams.set('redirect', pathname)
        const response = NextResponse.redirect(loginUrl)
        response.cookies.delete('mock-auth-session')
        return response
      }
    } catch (error) {
      // Invalid session format, redirect to login
      const loginUrl = new URL('/auth/login', request.url)
      loginUrl.searchParams.set('redirect', pathname)
      const response = NextResponse.redirect(loginUrl)
      response.cookies.delete('mock-auth-session')
      return response
    }
  }

  return NextResponse.next()
}

// Configure which routes to run proxy on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - api (API routes - these go directly to backend)
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!api|_next/static|_next/image|favicon.ico|.*\\.png$).*)',
  ],
}
