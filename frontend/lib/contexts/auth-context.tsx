"use client"

/**
 * Auth Context Provider
 *
 * Manages authentication state across the application.
 * Automatically switches between mock auth (development) and Supabase (production)
 * based on environment variables.
 */

import { createContext, useContext, useEffect, useState } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { logger } from '@/lib/logger'
import { mockAuth } from '@/lib/auth/mock-auth'
import { supabaseAuth } from '@/lib/auth/supabase-auth'
import type { User, Session, AuthError } from '@/lib/types'
import { useDependencySelection } from '@/hooks/use-dependency-selection'
import { useSidebar } from '@/hooks/use-sidebar'

// Determine which auth service to use based on environment
const hasSupabaseConfig =
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

// Force mock auth on localhost to avoid OAuth redirect issues
const isLocalhost = typeof window !== 'undefined' &&
  (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')

const authService = (hasSupabaseConfig && !isLocalhost) ? supabaseAuth : mockAuth

// Log which auth service is being used
if (typeof window !== 'undefined') {
  const usingMock = !hasSupabaseConfig || isLocalhost
  logger.log(
    `🔐 Auth Service: ${usingMock ? 'Mock' : 'Supabase'} ${
      isLocalhost ? '(localhost detected - using mock auth)' :
      hasSupabaseConfig ? '' : '(Set NEXT_PUBLIC_SUPABASE_URL to use Supabase)'
    }`
  )
}

interface AuthContextType {
  user: User | null
  session: Session | null
  loading: boolean
  signIn: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signUp: (email: string, password: string) => Promise<{ error: AuthError | null }>
  signInWithOAuth: (provider: 'google' | 'github') => Promise<{ error: AuthError | null }>
  signOut: () => Promise<void>
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

// Helper to set session cookie (for middleware access)
// Now async to ensure cookie is fully written before proceeding
async function setSessionCookie(session: Session | null): Promise<void> {
  if (typeof document === 'undefined') return

  if (session) {
    // Set cookie with same expiry as session
    const expires = new Date(session.expires_at)
    document.cookie = `mock-auth-session=${JSON.stringify(session)}; path=/; expires=${expires.toUTCString()}; SameSite=Lax`

    // Small delay to ensure cookie is fully written and readable
    // This prevents race conditions where middleware reads before cookie is available
    await new Promise(resolve => setTimeout(resolve, 50))

    // Verify cookie was set (defensive check)
    const cookieValue = document.cookie.split('; ').find(row => row.startsWith('mock-auth-session='))
    if (!cookieValue) {
      logger.warn('⚠️ Cookie was not set successfully')
    } else {
      logger.log('✓ Session cookie set and verified')
    }
  } else {
    // Clear cookie
    document.cookie = 'mock-auth-session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
    await new Promise(resolve => setTimeout(resolve, 50))
    logger.log('✓ Session cookie cleared')
  }
}

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [session, setSession] = useState<Session | null>(null)
  const [loading, setLoading] = useState(true)
  const queryClient = useQueryClient()

  // Track initialization state to prevent race conditions
  const [initialLoadComplete, setInitialLoadComplete] = useState(false)
  const [authListenerReady, setAuthListenerReady] = useState(false)

  // Initialize auth state on mount
  useEffect(() => {
    loadSession()
  }, [])

  // Subscribe to auth state changes (Supabase sessions)
  useEffect(() => {
    const { data: authListener } = authService.onAuthStateChange(async (event, session) => {
      logger.log('🔐 Auth state changed:', event, session?.user?.email)

      if (session) {
        setSession(session)
        setUser(session.user)
        await setSessionCookie(session)
      } else {
        setSession(null)
        setUser(null)
        await setSessionCookie(null)
      }

      // Mark listener as ready (but don't set loading=false yet)
      setAuthListenerReady(true)
    })

    // Cleanup subscription on unmount
    return () => {
      authListener?.subscription?.unsubscribe()
    }
  }, [])

  async function loadSession() {
    try {
      const { data } = await authService.getSession()
      if (data.session) {
        setSession(data.session)
        setUser(data.session.user)
        await setSessionCookie(data.session)
      }
    } catch (error) {
      logger.error('Failed to load session:', error)
    } finally {
      // Mark initial load as complete (but don't set loading=false yet)
      // Will only set loading=false when BOTH initial load AND auth listener are ready
      setInitialLoadComplete(true)
    }
  }

  // Only set loading=false when BOTH initial load and auth listener are ready
  // This prevents race conditions where the app redirects before session is fully loaded
  useEffect(() => {
    if (initialLoadComplete && authListenerReady) {
      logger.log('🔐 Auth initialization complete')
      setLoading(false)
    }
  }, [initialLoadComplete, authListenerReady])

  async function signIn(email: string, password: string) {
    try {
      // Clear all cached queries to ensure fresh data for new user
      queryClient.clear()

      const { user, session, error } = await authService.signInWithPassword({
        email,
        password,
      })

      if (error) {
        return { error }
      }

      setUser(user)
      setSession(session)
      await setSessionCookie(session)
      return { error: null }
    } catch (error) {
      logger.error('Sign in error:', error)
      return {
        error: {
          message: 'An unexpected error occurred',
          status: 500,
        },
      }
    }
  }

  async function signUp(email: string, password: string) {
    try {
      // Clear all cached queries to ensure fresh data for new user
      queryClient.clear()

      const { user, session, error } = await authService.signUp({
        email,
        password,
      })

      if (error) {
        return { error }
      }

      setUser(user)
      setSession(session)
      await setSessionCookie(session)
      return { error: null }
    } catch (error) {
      logger.error('Sign up error:', error)
      return {
        error: {
          message: 'An unexpected error occurred',
          status: 500,
        },
      }
    }
  }

  async function signInWithOAuth(provider: 'google' | 'github') {
    try {
      // Clear all cached queries to ensure fresh data for new user
      queryClient.clear()

      const { user, session, error } = await authService.signInWithOAuth({
        provider,
      })

      if (error) {
        return { error }
      }

      setUser(user)
      setSession(session)
      await setSessionCookie(session)
      return { error: null }
    } catch (error) {
      logger.error('OAuth sign in error:', error)
      return {
        error: {
          message: 'An unexpected error occurred',
          status: 500,
        },
      }
    }
  }

  async function signOut() {
    try {
      logger.log('🔐 Starting logout cleanup...')

      // Clear all cached queries before signing out (AWAIT to ensure completion)
      await queryClient.clear()
      logger.log('🔐 React Query cache cleared')

      // Clear dependency selection state
      useDependencySelection.getState().clearSelection()

      // Reset sidebar state
      useSidebar.getState().reset()
      logger.log('🔐 Sidebar state reset')

      // Defensively clear ALL persisted state from localStorage
      // This prevents stale state from affecting the next login
      if (typeof window !== 'undefined') {
        logger.log('🔐 Clearing localStorage items...')
        localStorage.removeItem('dependency-selection-storage')
        localStorage.removeItem('chat-sidebar-storage')

        // Clear any other persisted state that might exist
        const keysToRemove: string[] = []
        for (let i = 0; i < localStorage.length; i++) {
          const key = localStorage.key(i)
          if (key && (
            key.includes('storage') ||
            key.includes('state') ||
            key.includes('cache')
          ) && !key.includes('mock-auth')) {
            // Keep mock-auth-users and mock-auth-passwords for dev convenience
            keysToRemove.push(key)
          }
        }
        keysToRemove.forEach(key => {
          logger.log(`🔐 Removing: ${key}`)
          localStorage.removeItem(key)
        })
      }

      // Sign out from auth service
      await authService.signOut()

      // Clear React state
      setUser(null)
      setSession(null)
      await setSessionCookie(null)

      // Small delay to ensure all cleanup completes before navigation
      await new Promise(resolve => setTimeout(resolve, 100))

      logger.log('🔐 Logout cleanup complete')
    } catch (error) {
      logger.error('Sign out error:', error)
    }
  }

  const value: AuthContextType = {
    user,
    session,
    loading,
    signIn,
    signUp,
    signInWithOAuth,
    signOut,
  }

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}
