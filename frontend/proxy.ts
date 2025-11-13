import { createServerClient, type CookieOptions } from '@supabase/ssr'
import { NextResponse } from 'next/server'
import type { NextRequest } from 'next/server'

// Routes that require authentication
const protectedRoutes = ['/dashboard', '/upload', '/auth/profile']

// Check if Supabase is configured
const hasSupabaseConfig =
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

export async function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Check if this route needs protection
  const isProtectedRoute = protectedRoutes.some((route) =>
    pathname.startsWith(route)
  )

  // Allow public routes to pass through
  if (!isProtectedRoute) {
    return NextResponse.next()
  }

  // Use Supabase auth if configured, otherwise use mock auth
  if (hasSupabaseConfig) {
    return await handleSupabaseAuth(request)
  } else {
    return handleMockAuth(request)
  }
}

// Supabase authentication (production)
async function handleSupabaseAuth(request: NextRequest) {
  let response = NextResponse.next({
    request,
  })

  const supabase = createServerClient(
    process.env.NEXT_PUBLIC_SUPABASE_URL!,
    process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!,
    {
      cookies: {
        get(name: string) {
          return request.cookies.get(name)?.value
        },
        set(name: string, value: string, options: CookieOptions) {
          request.cookies.set(name, value)
          response = NextResponse.next({
            request,
          })
          response.cookies.set(name, value, options)
        },
        remove(name: string, options: CookieOptions) {
          request.cookies.set(name, '')
          response = NextResponse.next({
            request,
          })
          response.cookies.set(name, '', options)
        },
      },
    }
  )

  // CRITICAL: Call getUser() immediately after creating client
  // Do not run any code between createServerClient and getUser()
  const {
    data: { user },
  } = await supabase.auth.getUser()

  // Redirect to login if not authenticated
  if (!user) {
    const loginUrl = new URL('/auth/login', request.url)
    loginUrl.searchParams.set('redirect', request.nextUrl.pathname)
    return NextResponse.redirect(loginUrl)
  }

  // User is authenticated, allow access
  return response
}

// Mock authentication (development)
function handleMockAuth(request: NextRequest) {
  const { pathname } = request.nextUrl

  // Read session from cookie
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
