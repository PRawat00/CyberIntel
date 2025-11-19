/**
 * Chat API client for Phase 5 chat functionality.
 */

import { logger } from '@/lib/logger'
import type { ChatSession, ChatMessage } from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

/**
 * Get auth token - tries Supabase first, then falls back to mock auth
 */
async function getAuthToken(): Promise<string | null> {
  if (typeof window === 'undefined') {
    logger.log('[CHAT AUTH] Window is undefined, skipping auth')
    return null
  }

  // Try Supabase auth first
  if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    logger.log('[CHAT AUTH] Trying Supabase auth...')
    try {
      const { supabase } = await import('@/lib/supabase')
      if (supabase) {
        const { data } = await supabase.auth.getSession()
        logger.log('[CHAT AUTH] Supabase session data:', data.session ? 'Session found' : 'No session')
        if (data.session?.access_token) {
          logger.log('[CHAT AUTH] Supabase token found, length:', data.session.access_token.length)
          return data.session.access_token
        }
      } else {
        logger.log('[CHAT AUTH] Supabase client is null')
      }
    } catch (error) {
      logger.error('[CHAT AUTH] Failed to get Supabase session:', error)
    }
  } else {
    logger.log('[CHAT AUTH] Supabase not configured, env vars missing')
  }

  // Fallback to mock auth
  logger.log('[CHAT AUTH] Trying mock auth fallback...')
  const sessionData = localStorage.getItem('mock-auth-session')
  if (sessionData) {
    try {
      const session = JSON.parse(sessionData)
      logger.log('[CHAT AUTH] Mock token found')
      return session.token
    } catch {
      logger.log('[CHAT AUTH] Failed to parse mock session')
      return null
    }
  }

  logger.log('[CHAT AUTH] No auth token found')
  return null
}

/**
 * Get auth headers for API requests
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken()

  if (!token) {
    logger.warn('[CHAT AUTH HEADERS] No token available - request will be sent without authorization')
    return {}
  }

  logger.log('[CHAT AUTH HEADERS] Token obtained, creating Bearer header')
  logger.log('[CHAT AUTH HEADERS] Token preview:', token.substring(0, 30) + '...')
  logger.log('[CHAT AUTH HEADERS] Token length:', token.length)

  const headers = { Authorization: `Bearer ${token}` }
  logger.log('[CHAT AUTH HEADERS] Headers created:', Object.keys(headers))

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const error = await response.json().catch(() => ({
      error: "Unknown error",
      message: response.statusText,
    }))
    throw new Error(error.message || error.error || "API request failed")
  }
  return response.json()
}

export const chatApi = {
  /**
   * Create a new chat session
   */
  async createSession(scanId?: number, title?: string): Promise<ChatSession> {
    const authHeaders = await getAuthHeaders()
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        ...authHeaders,
      },
      body: JSON.stringify({
        scan_id: scanId,
        title: title,
      }),
    })
    return handleResponse<ChatSession>(response)
  },

  /**
   * Get or create a chat session for a scan
   */
  async getOrCreateSession(scanId?: number): Promise<ChatSession> {
    // First, try to get existing session for this scan
    if (scanId) {
      const sessions = await this.listSessions(scanId)
      if (sessions.length > 0) {
        return sessions[0] // Return most recent session
      }
    }
    // Create new session if none exists
    return this.createSession(scanId)
  },

  /**
   * List all chat sessions, optionally filtered by scan_id
   */
  async listSessions(scanId?: number): Promise<ChatSession[]> {
    const url = scanId
      ? `${API_BASE_URL}/api/chat/sessions?scan_id=${scanId}`
      : `${API_BASE_URL}/api/chat/sessions`

    const authHeaders = await getAuthHeaders()
    const response = await fetch(url, {
      headers: authHeaders,
    })
    return handleResponse<ChatSession[]>(response)
  },

  /**
   * Get a specific chat session
   */
  async getSession(sessionId: number): Promise<ChatSession> {
    const authHeaders = await getAuthHeaders()
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}`, {
      headers: authHeaders,
    })
    return handleResponse<ChatSession>(response)
  },

  /**
   * Get messages for a chat session
   */
  async getMessages(sessionId: number): Promise<ChatMessage[]> {
    const authHeaders = await getAuthHeaders()
    const response = await fetch(
      `${API_BASE_URL}/api/chat/sessions/${sessionId}/messages`,
      {
        headers: authHeaders,
      }
    )
    return handleResponse<ChatMessage[]>(response)
  },

  /**
   * Delete a chat session
   */
  async deleteSession(sessionId: number): Promise<void> {
    const authHeaders = await getAuthHeaders()
    const response = await fetch(`${API_BASE_URL}/api/chat/sessions/${sessionId}`, {
      method: "DELETE",
      headers: authHeaders,
    })
    await handleResponse<{ message: string }>(response)
  },

  /**
   * Get WebSocket URL for a session (with optional auth token)
   */
  async getWebSocketUrl(sessionId: number): Promise<string> {
    // Guard against SSR
    if (typeof window === "undefined") {
      return ""
    }

    const wsProtocol = window.location.protocol === "https:" ? "wss:" : "ws:"
    const apiUrl = API_BASE_URL.replace("http://", "").replace("https://", "")
    const baseUrl = `${wsProtocol}//${apiUrl}/api/chat/ws/${sessionId}`

    // Add auth token as query param for WebSocket
    const token = await getAuthToken()
    return token ? `${baseUrl}?token=${encodeURIComponent(token)}` : baseUrl
  },
}
