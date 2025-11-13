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
import { mockAuth } from '@/lib/auth/mock-auth'
import { supabaseAuth } from '@/lib/auth/supabase-auth'
import type { User, Session, AuthError } from '@/lib/types'
import { useDependencySelection } from '@/hooks/use-dependency-selection'

// Determine which auth service to use based on environment
const hasSupabaseConfig =
  process.env.NEXT_PUBLIC_SUPABASE_URL &&
  process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

const authService = hasSupabaseConfig ? supabaseAuth : mockAuth

// Log which auth service is being used
if (typeof window !== 'undefined') {
  console.log(
    `🔐 Auth Service: ${hasSupabaseConfig ? 'Supabase' : 'Mock'} ${
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
function setSessionCookie(session: Session | null) {
  if (typeof document === 'undefined') return

  if (session) {
    // Set cookie with same expiry as session
    const expires = new Date(session.expires_at)
    document.cookie = `mock-auth-session=${JSON.stringify(session)}; path=/; expires=${expires.toUTCString()}; SameSite=Lax`
  } else {
    // Clear cookie
    document.cookie = 'mock-auth-session=; path=/; expires=Thu, 01 Jan 1970 00:00:00 GMT'
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
    const { data: authListener } = authService.onAuthStateChange((event, session) => {
      console.log('🔐 Auth state changed:', event, session?.user?.email)

      if (session) {
        setSession(session)
        setUser(session.user)
        setSessionCookie(session)
      } else {
        setSession(null)
        setUser(null)
        setSessionCookie(null)
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
        setSessionCookie(data.session)
      }
    } catch (error) {
      console.error('Failed to load session:', error)
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
      console.log('🔐 Auth initialization complete')
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
      setSessionCookie(session)
      return { error: null }
    } catch (error) {
      console.error('Sign in error:', error)
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
      setSessionCookie(session)
      return { error: null }
    } catch (error) {
      console.error('Sign up error:', error)
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
      setSessionCookie(session)
      return { error: null }
    } catch (error) {
      console.error('OAuth sign in error:', error)
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
      // Clear all cached queries before signing out
      queryClient.clear()

      // Clear dependency selection state
      useDependencySelection.getState().clearSelection()

      // Defensively clear any persisted state from localStorage
      if (typeof window !== 'undefined') {
        localStorage.removeItem('dependency-selection-storage')
      }

      await authService.signOut()
      setUser(null)
      setSession(null)
      setSessionCookie(null)
    } catch (error) {
      console.error('Sign out error:', error)
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
