/**
 * Supabase client configuration for SecureChat
 * Handles authentication and database access
 */

import { createClient } from '@supabase/supabase-js'

const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY

// Check if Supabase is configured
const isSupabaseConfigured = !!(supabaseUrl && supabaseAnonKey)

// Log configuration status
if (!isSupabaseConfigured) {
  console.warn('⚠️  Supabase not configured - using mock authentication')
  console.warn('To use Supabase: Set NEXT_PUBLIC_SUPABASE_URL and NEXT_PUBLIC_SUPABASE_ANON_KEY')
  console.warn('See .env.example for details')
}

/**
 * Supabase client instance
 * Configured with:
 * - Auto token refresh
 * - Session persistence in localStorage
 * - URL-based session detection (for OAuth callbacks)
 *
 * Will be null if Supabase environment variables are not set (falls back to mock auth)
 */
export const supabase = isSupabaseConfigured
  ? createClient(supabaseUrl!, supabaseAnonKey!, {
      auth: {
        autoRefreshToken: true,
        persistSession: true,
        detectSessionInUrl: true,
        storage: typeof window !== 'undefined' ? window.localStorage : undefined,
      },
    })
  : null

/**
 * Helper function to get current session
 * @returns Current session or null
 */
export async function getSession() {
  if (!supabase) return null

  const { data: { session }, error } = await supabase.auth.getSession()
  if (error) {
    console.error('Error getting session:', error)
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
    console.error('Error signing out:', error)
    throw error
  }
}
