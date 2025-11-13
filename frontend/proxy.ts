import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/upload', '/auth/profile']

/**
 * Next.js 16 Proxy Function
 *
 * Handles authentication for protected routes using cookie-based session validation.
 * Works with both mock auth (development) and client-side Supabase auth (production).
 */
export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if this route needs protection
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  // Allow public routes to pass through
  if (!isProtectedRoute) {
    return NextResponse.next()
  }

  // Read session from cookie (works for both mock and Supabase client-side auth)
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
    return NextResponse.next()
  } catch (error) {
    // Invalid session cookie, redirect to login and clear cookie
    console.error('Invalid session cookie:', error)
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
