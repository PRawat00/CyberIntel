/**
 * API client for communicating with the FastAPI backend.
 */

import type {
  ScanDetail,
  ScanListResponse,
  Stats,
  Dependency,
  SeverityLevel,
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
 */
async function getAuthToken(): Promise<string | null> {
  if (typeof window === 'undefined') {
    console.log('[AUTH] Window is undefined, skipping auth')
    return null
  }

  // Try Supabase auth first
  if (process.env.NEXT_PUBLIC_SUPABASE_URL && process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY) {
    console.log('[AUTH] Trying Supabase auth...')
    try {
      const { supabase } = await import('@/lib/supabase')
      if (supabase) {
        const { data } = await supabase.auth.getSession()
        console.log('[AUTH] Supabase session data:', data.session ? 'Session found' : 'No session')
        if (data.session?.access_token) {
          console.log('[AUTH] Supabase token found, length:', data.session.access_token.length)
          return data.session.access_token
        }
      } else {
        console.log('[AUTH] Supabase client is null')
      }
    } catch (error) {
      console.error('[AUTH] Failed to get Supabase session:', error)
      // Continue to mock auth fallback
    }
  } else {
    console.log('[AUTH] Supabase not configured, env vars missing')
  }

  // Fallback to mock auth
  console.log('[AUTH] Trying mock auth fallback...')
  const mockSession = localStorage.getItem('mock-auth-session')
  if (mockSession) {
    try {
      const session = JSON.parse(mockSession)
      console.log('[AUTH] Mock token found')
      return session.token
    } catch {
      console.log('[AUTH] Failed to parse mock session')
      return null
    }
  }

  console.log('[AUTH] No auth token found')
  return null
}

/**
 * Get auth headers for API requests
 */
async function getAuthHeaders(): Promise<HeadersInit> {
  const token = await getAuthToken()

  if (!token) {
    console.warn('[AUTH HEADERS] No token available - request will be sent without authorization')
    return {}
  }

  // Log token details for debugging
  console.log('[AUTH HEADERS] Token obtained, creating Bearer header')
  console.log('[AUTH HEADERS] Token preview:', token.substring(0, 30) + '...')
  console.log('[AUTH HEADERS] Token length:', token.length)

  const headers = { Authorization: `Bearer ${token}` }
  console.log('[AUTH HEADERS] Headers created:', Object.keys(headers))

  return headers
}

async function handleResponse<T>(response: Response): Promise<T> {
  if (!response.ok) {
    console.error('[API] Request failed:')
    console.error('[API]   Status:', response.status)
    console.error('[API]   Status Text:', response.statusText)
    console.error('[API]   URL:', response.url)

    const error = await response.json().catch(() => ({
      error: "Unknown error",
      message: `HTTP ${response.status}: ${response.statusText}`,
    }))

    console.error('[API]   Error details:', error)

    // Special handling for authentication errors
    if (response.status === 401) {
      console.error('[API] Authentication failed - token may be expired or invalid')
    } else if (response.status === 403) {
      console.error('[API] Authorization failed - insufficient permissions')
    } else if (response.status === 404) {
      console.error('[API] 404 Not Found - this could be a routing issue or auth dependency failure')
    }

    throw new APIError(response.status, error.message || error.detail, error.details)
  }

  return response.json()
}

export const api = {
  /**
   * Upload and scan a dependency file.
   */
  async uploadScan(file: File): Promise<ScanDetail> {
    const formData = new FormData()
    formData.append("file", file)

    const authHeaders = await getAuthHeaders()
    const url = `${API_BASE_URL}/api/scans`

    console.log('[UPLOAD] ====== FILE UPLOAD DEBUG ======')
    console.log('[UPLOAD] Starting file upload...')
    console.log('[UPLOAD] File name:', file.name)
    console.log('[UPLOAD] File size:', file.size, 'bytes')
    console.log('[UPLOAD] File type:', file.type || 'not specified')
    console.log('[UPLOAD] API URL:', url)
    console.log('[UPLOAD] Auth headers present:', Object.keys(authHeaders))
    console.log('[UPLOAD] Has Authorization header:', 'Authorization' in authHeaders)

    if ('Authorization' in authHeaders) {
      const authHeader = (authHeaders as any).Authorization
      console.log('[UPLOAD] Auth header format:', authHeader.startsWith('Bearer ') ? 'Bearer token' : 'Unknown format')
      console.log('[UPLOAD] Token preview:', authHeader.substring(0, 50) + '...')
    } else {
      console.warn('[UPLOAD] ⚠️ No Authorization header - request will likely fail with 401')
    }

    console.log('[UPLOAD] Sending request...')

    const response = await fetch(url, {
      method: "POST",
      headers: {
        ...authHeaders,
      },
      body: formData,
    })

    console.log('[UPLOAD] Response received:')
    console.log('[UPLOAD]   Status:', response.status)
    console.log('[UPLOAD]   Status Text:', response.statusText)
    console.log('[UPLOAD]   Response Type:', response.type)
    console.log('[UPLOAD] ================================')

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
    console.log('[API] Getting stats from:', `${API_BASE_URL}/api/stats`)
    console.log('[API] Auth headers:', headers)

    const response = await fetch(`${API_BASE_URL}/api/stats`, {
      headers,
    })

    console.log('[API] Stats response status:', response.status)
    if (!response.ok) {
      const errorText = await response.text()
      console.error('[API] Stats error response:', errorText)
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
}

export { APIError }
