/**
 * Supabase Auth Adapter
 *
 * Provides a consistent authentication interface that matches the mock auth service.
 * Drop-in replacement for mock-auth.ts in production.
 *
 * Usage:
 * Replace: import { mockAuth } from '@/lib/auth/mock-auth'
 * With: import { supabaseAuth as mockAuth } from '@/lib/auth/supabase-auth'
 */

import { supabase } from '@/lib/supabase'
import type { User, Session, AuthError } from '@/lib/types'
import type { User as SupabaseUser, Session as SupabaseSession } from '@supabase/supabase-js'

/**
 * Convert Supabase User to our User type
 */
function mapSupabaseUser(supabaseUser: SupabaseUser | null): User | null {
  if (!supabaseUser) return null

  return {
    id: supabaseUser.id,
    email: supabaseUser.email || '',
    user_metadata: {
      provider: (supabaseUser.app_metadata?.provider as 'email' | 'google' | 'github') || 'email',
      full_name: supabaseUser.user_metadata?.full_name || supabaseUser.user_metadata?.name || supabaseUser.email?.split('@')[0] || 'User',
      avatar_url: supabaseUser.user_metadata?.avatar_url || null,
    },
    created_at: supabaseUser.created_at || new Date().toISOString(),
  }
}

/**
 * Convert Supabase Session to our Session type
 */
function mapSupabaseSession(supabaseSession: SupabaseSession | null): Session | null {
  if (!supabaseSession) return null

  const user = mapSupabaseUser(supabaseSession.user)
  if (!user) return null

  return {
    user,
    token: supabaseSession.access_token,
    expires_at: new Date(supabaseSession.expires_at! * 1000).toISOString(),
  }
}

/**
 * Convert Supabase error to our AuthError type
 */
function mapSupabaseError(error: any): AuthError {
  return {
    message: error.message || 'Authentication error',
    status: error.status || 500,
  }
}

class SupabaseAuthAdapter {
  /**
   * Get current session
   */
  async getSession(): Promise<{ data: { session: Session | null } }> {
    if (!supabase) {
      return { data: { session: null } }
    }

    try {
      const { data, error } = await supabase.auth.getSession()
      if (error) {
        console.error('getSession error:', error)
        return { data: { session: null } }
      }

      return {
        data: {
          session: mapSupabaseSession(data.session),
        },
      }
    } catch (error) {
      console.error('getSession exception:', error)
      return { data: { session: null } }
    }
  }

  /**
   * Sign in with email and password
   */
  async signInWithPassword({ email, password }: { email: string; password: string }): Promise<{
    user: User | null
    session: Session | null
    error: AuthError | null
  }> {
    if (!supabase) {
      return {
        user: null,
        session: null,
        error: { message: 'Supabase not configured', status: 500 },
      }
    }

    try {
      const { data, error } = await supabase.auth.signInWithPassword({
        email,
        password,
      })

      if (error) {
        return {
          user: null,
          session: null,
          error: mapSupabaseError(error),
        }
      }

      return {
        user: mapSupabaseUser(data.user),
        session: mapSupabaseSession(data.session),
        error: null,
      }
    } catch (error: any) {
      return {
        user: null,
        session: null,
        error: mapSupabaseError(error),
      }
    }
  }

  /**
   * Sign up with email and password
   */
  async signUp({ email, password }: { email: string; password: string }): Promise<{
    user: User | null
    session: Session | null
    error: AuthError | null
  }> {
    if (!supabase) {
      return {
        user: null,
        session: null,
        error: { message: 'Supabase not configured', status: 500 },
      }
    }

    try {
      const { data, error } = await supabase.auth.signUp({
        email,
        password,
        options: {
          // Email confirmation settings (controlled by Supabase dashboard)
          emailRedirectTo: typeof window !== 'undefined' ? window.location.origin : undefined,
        },
      })

      if (error) {
        return {
          user: null,
          session: null,
          error: mapSupabaseError(error),
        }
      }

      // Note: If email confirmation is required, session will be null
      // User needs to confirm email before they can sign in
      return {
        user: mapSupabaseUser(data.user),
        session: mapSupabaseSession(data.session),
        error: null,
      }
    } catch (error: any) {
      return {
        user: null,
        session: null,
        error: mapSupabaseError(error),
      }
    }
  }

  /**
   * Sign in with OAuth provider (Google, GitHub, etc.)
   */
  async signInWithOAuth({ provider }: { provider: 'google' | 'github' }): Promise<{
    user: User | null
    session: Session | null
    error: AuthError | null
  }> {
    if (!supabase) {
      return {
        user: null,
        session: null,
        error: { message: 'Supabase not configured', status: 500 },
      }
    }

    try {
      const { data, error } = await supabase.auth.signInWithOAuth({
        provider,
        options: {
          redirectTo: typeof window !== 'undefined' ? `${window.location.origin}/auth/callback` : undefined,
        },
      })

      if (error) {
        return {
          user: null,
          session: null,
          error: mapSupabaseError(error),
        }
      }

      // OAuth sign-in redirects immediately, so we won't have user/session here
      // The callback page will handle the session
      return {
        user: null,
        session: null,
        error: null,
      }
    } catch (error: any) {
      return {
        user: null,
        session: null,
        error: mapSupabaseError(error),
      }
    }
  }

  /**
   * Sign out
   */
  async signOut(): Promise<void> {
    if (!supabase) {
      throw new Error('Supabase not configured')
    }

    try {
      const { error } = await supabase.auth.signOut()
      if (error) {
        console.error('signOut error:', error)
        throw error
      }
    } catch (error) {
      console.error('signOut exception:', error)
      throw error
    }
  }

  /**
   * Listen to auth state changes
   * @param callback Function to call when auth state changes
   */
  onAuthStateChange(callback: (event: string, session: Session | null) => void) {
    if (!supabase) {
      // Return a no-op unsubscribe function
      return { data: { subscription: { unsubscribe: () => {} } } }
    }

    return supabase.auth.onAuthStateChange((event, supabaseSession) => {
      const session = mapSupabaseSession(supabaseSession)
      callback(event, session)
    })
  }
}

// Export singleton instance
export const supabaseAuth = new SupabaseAuthAdapter()

// Also export as default for easier importing
export default supabaseAuth
