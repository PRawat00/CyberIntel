/**
 * TypeScript types for the SecureChat application.
 */

export interface CVE {
  cve_id: string
  severity: string
  cvss_score?: number
  description: string
  published_date?: string
  vendor?: string
  product?: string
  affected_version?: string
}

export interface Dependency {
  id: number
  package_name: string
  version: string
  ecosystem: string
  is_vulnerable: boolean
  cve_count: number
  highest_severity?: string
  cves: CVE[]
}

export interface SeverityCount {
  critical: number
  high: number
  medium: number
  low: number
}

export interface ScanSummary {
  id: number
  file_name: string
  file_type: string
  scan_date: string
  total_dependencies: number
  vulnerable_dependencies: number
  total_cves: number
  severity_counts: SeverityCount
}

export interface ScanDetail extends ScanSummary {
  dependencies: Dependency[]
}

export interface ScanListResponse {
  scans: ScanSummary[]
  total: number
  page: number
  per_page: number
  pages: number
}

export interface Stats {
  total_scans: number
  total_dependencies_scanned: number
  total_vulnerabilities_found: number
  critical_vulnerabilities: number
  recent_scans: ScanSummary[]
}

export interface ErrorResponse {
  error: string
  message: string
  details?: Record<string, unknown>
}

export type SeverityLevel = "Critical" | "High" | "Medium" | "Low"
export type FileType = "npm" | "pip" | "go" | "ruby" | "maven"

// Chat types (Phase 5)
export interface ChatSession {
  id: number
  scan_id?: number
  title?: string
  session_type: "general" | "project"
  selected_dependency_ids?: number[]  // NEW: Selected dependencies for context
  context_injected?: boolean  // NEW: Whether full context was injected
  created_at: string
  last_message_at: string
  message_count: number
}

export interface ChatMessage {
  id: number
  session_id: number
  role: "user" | "assistant"
  content: string
  context_cves?: string[]
  input_tokens?: number
  output_tokens?: number
  created_at: string
}

export interface WebSocketMessage {
  type: "start" | "chunk" | "end" | "error" | "context_updated" | "context_cleared"  // NEW: Added context message types
  content?: string
  message_id?: number
  error?: string
  dependency_ids?: number[]  // NEW: For sending context with messages
}

// Auth types
export interface User {
  id: string
  email: string
  user_metadata: {
    provider: 'email' | 'google' | 'github'
    full_name?: string
    avatar_url?: string
  }
  created_at: string
}

export interface Session {
  user: User
  token: string
  expires_at: string
}

export interface AuthError {
  message: string
  status?: number
}
