/**
 * Next.js Middleware for Route Protection
 *
 * Protects routes that require authentication.
 * Redirects unauthenticated users to login page.
 */

import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/upload', '/auth/profile']

// Public routes (accessible without auth)
const publicRoutes = ['/', '/auth/login', '/auth/signup']

export function middleware(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if route requires authentication
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  if (!isProtectedRoute) {
    return NextResponse.next()
  }

  // Check for auth session in cookies
  const sessionCookie = request.cookies.get('mock-auth-session')

  // For mock auth, we also check localStorage via client-side redirect
  // Since middleware runs on the server, we can't access localStorage directly
  // So we'll use a cookie-based approach or client-side protection

  // If no session cookie, redirect to login
  if (!sessionCookie) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', pathname)
    return NextResponse.redirect(loginUrl)
  }

  // Verify session is valid (not expired)
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

  return NextResponse.next()
}

// Configure which routes to run middleware on
export const config = {
  matcher: [
    /*
     * Match all request paths except:
     * - _next/static (static files)
     * - _next/image (image optimization files)
     * - favicon.ico (favicon file)
     * - public folder
     */
    '/((?!_next/static|_next/image|favicon.ico|.*\\.png$).*)',
  ],
}
