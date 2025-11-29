/**
 * Supabase client configuration for SecureChat
 * Handles authentication and database access
 *
 * Uses @supabase/ssr for proper cookie-based session management
 * that works with server-side rendering and middleware.
 */

import { createBrowserClient } from '@supabase/ssr'
import { logger } from '@/lib/logger'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

// Check if Supabase is configured
const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey)

// Log configuration status
if (!isSupabaseConfigured) {
  logger.warn('Supabase not configured - using mock authentication')
  logger.warn('To use Supabase: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
}

/**
 * Supabase client instance
 * Configured with:
 * - Cookie-based session storage (works with SSR)
 * - Auto token refresh via middleware
 * - Shared session between server and client
 *
 * Will be null if Supabase environment variables are not set (falls back to mock auth)
 */
export const supabase = isSupabaseConfigured
  ? createBrowserClient(supabaseUrl!, supabaseAnonKey!)
  : null

/**
 * Helper function to get current session
 * @returns Current session or null
 */
export async function getSession() {
  if (!supabase) return null

  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) {
    logger.error('Error getting session:', error)
    return null
  }
  return session
}

/**
 * Helper function to get current user
 * @returns Current user or null
 */
export async function getUser() {
  const session = await getSession()
  return session?.user ?? null
}

/**
 * Helper function to get auth token for API calls
 * @returns Bearer token string or null
 */
export async function getAuthToken() {
  const session = await getSession()
  return session?.access_token ?? null
}

/**
 * Helper function to sign out
 */
export async function signOut() {
  if (!supabase) {
    throw new Error('Supabase client not initialized')
  }

  const { error } = await supabase.auth.signOut()
  if (error) {
    logger.error('Error signing out:', error)
    throw error
  }
}
