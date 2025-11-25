/**
 * API client for communicating with the FastAPI backend.
 * Automatically falls back to mock API when backend is unavailable.
 */

import { logger } from '@/lib/logger'
import type {
  ScanDetail,
  ScanListResponse,
  Stats,
  Dependency,
  SeverityLevel,
  GitHubConnection,
  GitHubRepoOption,
  GitHubSyncResult,
} from "./types"

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"

class APIError extends Error {
  constructor(
    public status: number,
    message: string,
    public details?: unknown
  ) {
    super(message)
    this.name = "APIError"
  }
}

/**
 * Get auth token from localStorage
 * Works with both mock auth and Supabase auth
 * Includes retry mechanism to handle race conditions after login
 */
async function getAuthToken(retryCount = 0, maxRetries = 3): Promise<string | null> {
  const delay = (ms: number) => new Promise(resolve => setTimeout(resolve, ms))
  if (typeof window === 'undefined') {
    logger.log('[AUTH] Window is undefined, skipping auth')
    return null
  }

  // Try Supabase auth first
  if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    logger.log('[AUTH] Trying Supabase auth...')
    try {
      const { supabase } = await import('@/lib/supabase')
      if (supabase) {
        const { data } = await supabase.auth.getSession()
        logger.log('[AUTH] Supabase session data:', data.session ? 'Session found' : 'No session')
        if (data.session?.access_token) {
          logger.log('[AUTH] Supabase token found, length:', data.session.access_token.length)
          return data.session.access_token
        }
      } else {
        logger.log('[AUTH] Supabase client is null')
      }
    } catch (error) {
      logger.error('[AUTH] Failed to get Supabase session:', error)
      // Continue to mock auth fallback
    }
  } else {
    logger.log('[AUTH] Supabase not configured, env vars missing')
  }

  // Fallback to mock auth
  logger.log('[AUTH] Trying mock auth fallback...')
  const mockSession = localStorage.getItem('mock-auth-session')
  if (mockSession) {
    try {
      const session = JSON.parse(mockSession)
      logger.log('[AUTH] Mock token found')
      return session.token
    } catch {
      logger.log('[AUTH] Failed to parse mock session')
      return null
    }
  }

  // If no token found and we haven't exhausted retries, wait and try again
  // This handles race conditions where the token hasn't been written to storage yet
  if (retryCount < maxRetries) {
    const waitTime = Math.min(100 * Math.pow(2, retryCount), 500) // Exponential backoff: 100ms, 200ms, 400ms
    logger.log(`[AUTH] No token found, retrying in ${waitTime}ms (attempt ${retryCount + 1}/${maxRetries})`)
    await delay(waitTime)
    return getAuthToken(retryCount + 1, maxRetries)
  }

  logger.log('[AUTH] No auth token found after all retries')
  return null
}

/**
 * Get auth headers for API requests
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken()

  if (!token) {
    logger.warn('[AUTH HEADERS] No token available - request will be sent without authorization')
    return {}
  }

  // Log token details for debugging
  logger.log('[AUTH HEADERS] Token obtained, creating Bearer header')
  logger.log('[AUTH HEADERS] Token preview:', token.substring(0, 30) + '...')
  logger.log('[AUTH HEADERS] Token length:', token.length)

  const headers = { Authorization: `Bearer ${token}` }
  logger.log('[AUTH HEADERS] Headers created:', Object.keys(headers))

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    logger.error('[API] Request failed:')
    logger.error('[API]   Status:', response.status)
    logger.error('[API]   Status Text:', response.statusText)
    logger.error('[API]   URL:', response.url)

    const error = await response.json().catch(() => ({
      error: "Unknown error",
      message: `HTTP ${response.status}: ${response.statusText}`,
    }))

    logger.error('[API]   Error details:', error)

    // Special handling for authentication errors
    if (response.status === 401) {
      logger.error('[API] Authentication failed - token may be expired or invalid')
    } else if (response.status === 403) {
      logger.error('[API] Authorization failed - insufficient permissions')
    } else if (response.status === 404) {
      logger.error('[API] 404 Not Found - this could be a routing issue or auth dependency failure')
    }

    throw new APIError(response.status, error.message || error.detail, error.details)
  }

  return response.json()
}

export const api = {
  /**
   * Generic GET request.
   */
  async get<T = any>(endpoint: string): Promise<T> {
    const url = endpoint.startsWith('/') ? `${API_BASE_URL}/api${endpoint}` : `${API_BASE_URL}${endpoint}`
    const response = await fetch(url, {
      method: "GET",
      headers: await getAuthHeaders(),
    })
    return handleResponse<T>(response)
  },

  /**
   * Generic POST request.
   */
  async post<T = any>(endpoint: string, data?: unknown): Promise<T> {
    const url = endpoint.startsWith('/') ? `${API_BASE_URL}/api${endpoint}` : `${API_BASE_URL}${endpoint}`
    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...await getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: data ? JSON.stringify(data) : undefined,
    })
    return handleResponse<T>(response)
  },

  /**
   * Upload and scan a dependency file.
   */
  async uploadScan(file: File): Promise<ScanDetail> {
    const formData = new FormData()
    formData.append("file", file)

    const authHeaders = await getAuthHeaders()
    const url = `${API_BASE_URL}/api/scans`

    logger.log('[UPLOAD] ====== FILE UPLOAD DEBUG ======')
    logger.log('[UPLOAD] Starting file upload...')
    logger.log('[UPLOAD] File name:', file.name)
    logger.log('[UPLOAD] File size:', file.size, 'bytes')
    logger.log('[UPLOAD] File type:', file.type || 'not specified')
    logger.log('[UPLOAD] API URL:', url)
    logger.log('[UPLOAD] Auth headers present:', Object.keys(authHeaders))
    logger.log('[UPLOAD] Has Authorization header:', 'Authorization' in authHeaders)

    if ('Authorization' in authHeaders) {
      const authHeader = (authHeaders as any).Authorization
      logger.log('[UPLOAD] Auth header format:', authHeader.startsWith('Bearer ') ? 'Bearer token' : 'Unknown format')
      logger.log('[UPLOAD] Token preview:', authHeader.substring(0, 50) + '...')
    } else {
      logger.error('[UPLOAD] No Authorization header - cannot proceed with upload')
      throw new APIError(
        401,
        'Authentication required. Please ensure you are logged in and try again.',
        { reason: 'No auth token available after retries' }
      )
    }

    logger.log('[UPLOAD] Sending request...')

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...authHeaders,
      },
      body: formData,
    })

    logger.log('[UPLOAD] Response received:')
    logger.log('[UPLOAD]   Status:', response.status)
    logger.log('[UPLOAD]   Status Text:', response.statusText)
    logger.log('[UPLOAD]   Response Type:', response.type)
    logger.log('[UPLOAD] ================================')

    return handleResponse<ScanDetail>(response)
  },

  /**
   * Get list of scans with pagination.
   */
  async listScans(params?: {
    page?: number
    per_page?: number
    file_type?: string
  }): Promise<ScanListResponse> {
    const searchParams = new URLSearchParams()
    if (params?.page) searchParams.set("page", params.page.toString())
    if (params?.per_page)
      searchParams.set("per_page", params.per_page.toString())
    if (params?.file_type) searchParams.set("file_type", params.file_type)

    const response = await fetch(
      `${API_BASE_URL}/api/scans?${searchParams.toString()}`,
      {
        headers: await getAuthHeaders(),
      }
    )

    return handleResponse<ScanListResponse>(response)
  },

  /**
   * Get detailed scan results by ID.
   */
  async getScan(scanId: number): Promise<ScanDetail> {
    const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, {
      headers: await getAuthHeaders(),
    })
    return handleResponse<ScanDetail>(response)
  },

  /**
   * Get dependencies for a specific scan.
   */
  async getScanDependencies(
    scanId: number,
    params?: {
      vulnerable_only?: boolean
      severity_min?: SeverityLevel
    }
  ): Promise<Dependency[]> {
    const searchParams = new URLSearchParams()
    if (params?.vulnerable_only)
      searchParams.set("vulnerable_only", "true")
    if (params?.severity_min)
      searchParams.set("severity_min", params.severity_min)

    const response = await fetch(
      `${API_BASE_URL}/api/scans/${scanId}/dependencies?${searchParams.toString()}`,
      {
        headers: await getAuthHeaders(),
      }
    )

    return handleResponse<Dependency[]>(response)
  },

  /**
   * Export scan results.
   */
  async exportScan(
    scanId: number,
    format: "json" | "csv" | "html"
  ): Promise<Blob> {
    const response = await fetch(
      `${API_BASE_URL}/api/scans/${scanId}/export?format=${format}`,
      {
        headers: await getAuthHeaders(),
      }
    )

    if (!response.ok) {
      throw new Error(`Export failed: ${response.statusText}`)
    }

    return response.blob()
  },

  /**
   * Delete a scan.
   */
  async deleteScan(scanId: number): Promise<void> {
    const response = await fetch(`${API_BASE_URL}/api/scans/${scanId}`, {
      method: "DELETE",
      headers: await getAuthHeaders(),
    })

    if (!response.ok) {
      throw new Error(`Delete failed: ${response.statusText}`)
    }
  },

  /**
   * Get dashboard statistics.
   */
  async getStats(): Promise<Stats> {
    const headers = await getAuthHeaders()
    logger.log('[API] Getting stats from:', `${API_BASE_URL}/api/stats`)
    logger.log('[API] Auth headers:', headers)

    const response = await fetch(`${API_BASE_URL}/api/stats`, {
      headers,
    })

    logger.log('[API] Stats response status:', response.status)
    if (!response.ok) {
      const errorText = await response.text()
      logger.error('[API] Stats error response:', errorText)
    }

    return handleResponse<Stats>(response)
  },

  /**
   * Health check.
   */
  async healthCheck(): Promise<{ status: string; version: string }> {
    const response = await fetch(`${API_BASE_URL}/health`)
    return handleResponse(response)
  },

  /**
   * Get a sample file for demo purposes.
   */
  async getSampleFile(filename: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}/api/samples/${filename}`)

    if (!response.ok) {
      throw new APIError(
        response.status,
        `Failed to fetch sample file: ${response.statusText}`
      )
    }

    return response.blob()
  },

  // =====================
  // GitHub Integration
  // =====================

  /**
   * Get GitHub OAuth authorization URL.
   */
  async getGitHubAuthUrl(): Promise<{ url: string; state: string }> {
    const response = await fetch(`${API_BASE_URL}/api/github/oauth/authorize`, {
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * Handle GitHub OAuth callback.
   */
  async handleGitHubCallback(code: string, state: string): Promise<{ success: boolean; message: string; github_username?: string }> {
    const response = await fetch(`${API_BASE_URL}/api/github/oauth/callback`, {
      method: "POST",
      headers: {
        ...await getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ code, state }),
    })
    return handleResponse(response)
  },

  /**
   * Get GitHub connection status.
   */
  async getGitHubConnection(): Promise<GitHubConnection> {
    const response = await fetch(`${API_BASE_URL}/api/github/connection`, {
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * Disconnect GitHub integration.
   */
  async disconnectGitHub(): Promise<{ success: boolean; message: string }> {
    const response = await fetch(`${API_BASE_URL}/api/github/connection`, {
      method: "DELETE",
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * List available GitHub repositories.
   */
  async getGitHubRepos(): Promise<{ success: boolean; repositories: GitHubRepoOption[] }> {
    const response = await fetch(`${API_BASE_URL}/api/github/repos`, {
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * Set which repository to track.
   */
  async setGitHubRepo(repoFullName: string): Promise<{ success: boolean; message: string; repo_full_name?: string }> {
    const response = await fetch(`${API_BASE_URL}/api/github/repo`, {
      method: "POST",
      headers: {
        ...await getAuthHeaders(),
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ repo_full_name: repoFullName }),
    })
    return handleResponse(response)
  },

  /**
   * Sync GitHub repository.
   */
  async syncGitHub(): Promise<GitHubSyncResult> {
    const response = await fetch(`${API_BASE_URL}/api/github/sync`, {
      method: "POST",
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * Toggle auto-sync on login setting.
   */
  async toggleGitHubAutoSync(): Promise<{ success: boolean; auto_sync_enabled: boolean }> {
    const response = await fetch(`${API_BASE_URL}/api/github/sync/toggle-auto`, {
      method: "POST",
      headers: await getAuthHeaders(),
    })
    return handleResponse(response)
  },

  /**
   * Check if GitHub OAuth is configured.
   */
  async getGitHubOAuthStatus(): Promise<{ configured: boolean; callback_url?: string }> {
    const response = await fetch(`${API_BASE_URL}/api/github/oauth/status`)
    return handleResponse(response)
  },
}

export { APIError }
