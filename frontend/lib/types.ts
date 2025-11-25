/**
 * TypeScript types for the SecureChat application.
 */

import { SimulationNodeDatum, SimulationLinkDatum } from 'd3'

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

// Usage Analysis Types (for Code Impact feature)
export interface CodeUsage {
  isUsed: boolean
  impactScore: 'HIGH' | 'MEDIUM' | 'LOW' | 'NONE'
  locations: UsageLocation[]
}

export interface UsageLocation {
  file: string
  line: number
  snippet: string
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
  // Extended fields for new features
  usage?: CodeUsage
  license?: string
  type?: 'direct' | 'transitive' | 'dev'
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
  // GitHub source tracking
  source: 'upload' | 'github'
  github_repo?: string
  github_path?: string
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

// Graph Visualization Types (for D3 Network Graph)
export interface GraphNode extends SimulationNodeDatum {
  id: string
  group: number // 1: Root, 2: Direct, 3: Transitive
  status: 'safe' | 'warning' | 'critical'
  data: Dependency
  // Explicitly defining these for stricter type safety with D3
  x?: number
  y?: number
  vx?: number
  vy?: number
  fx?: number | null
  fy?: number | null
  index?: number
}

export interface GraphLink extends SimulationLinkDatum<GraphNode> {
  source: string | GraphNode
  target: string | GraphNode
}

export interface GraphData {
  nodes: GraphNode[]
  links: GraphLink[]
}

// Reports Types (for License Analysis and Compliance)
export interface LicenseDistribution {
  license: string
  count: number
  percentage: number
}

export interface RiskFactor {
  title: string
  description: string
  severity: 'high' | 'medium' | 'low'
  count: number
}

export interface SecurityReport {
  security_score: number
  license_risk: 'low' | 'medium' | 'high'
  policy_status: 'passed' | 'failed' | 'warning'
  license_distribution: LicenseDistribution[]
  risk_factors: RiskFactor[]
}

// Integration Types
export interface Integration {
  id: string
  name: string
  type: 'github' | 'slack' | 'jira' | 'other'
  status: 'connected' | 'disconnected' | 'error'
  config?: Record<string, unknown>
  last_sync?: string
}

// GitHub Integration Types
export interface GitHubConnection {
  id: number | null
  github_username: string | null
  github_avatar_url?: string | null
  is_active: boolean
  auto_sync_enabled: boolean
  last_sync_at?: string | null
  repo_full_name?: string | null
  sync_error?: string | null
}

export interface GitHubRepoOption {
  full_name: string
  name: string
  owner: string
  is_private: boolean
  default_branch: string
  description?: string | null
}

export interface GitHubSyncResult {
  success: boolean
  message?: string
  error?: string
  files_found: number
  scans_created: number
}
