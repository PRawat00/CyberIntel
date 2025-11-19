/**
 * Mock API Service
 * Provides realistic mock data when backend is unavailable
 * Enables full frontend testing without running the Python backend
 */

import type { Stats, ScanSummary, ScanDetail, ScanListResponse, Dependency } from './types'

// Generate realistic mock scans
function generateMockScans(): ScanSummary[] {
  return [
    {
      id: 1,
      file_name: 'vulnerable-app-package.json',
      file_type: 'npm',
      scan_date: new Date(Date.now() - 2 * 60 * 60 * 1000).toISOString(),
      total_dependencies: 45,
      vulnerable_dependencies: 12,
      total_cves: 18,
      severity_counts: {
        critical: 3,
        high: 5,
        medium: 7,
        low: 3,
      },
    },
    {
      id: 2,
      file_name: 'production-requirements.txt',
      file_type: 'pip',
      scan_date: new Date(Date.now() - 24 * 60 * 60 * 1000).toISOString(),
      total_dependencies: 32,
      vulnerable_dependencies: 3,
      total_cves: 4,
      severity_counts: {
        critical: 0,
        high: 1,
        medium: 2,
        low: 1,
      },
    },
    {
      id: 3,
      file_name: 'legacy-project-package-lock.json',
      file_type: 'npm',
      scan_date: new Date(Date.now() - 7 * 24 * 60 * 60 * 1000).toISOString(),
      total_dependencies: 156,
      vulnerable_dependencies: 28,
      total_cves: 42,
      severity_counts: {
        critical: 7,
        high: 12,
        medium: 15,
        low: 8,
      },
    },
  ]
}

// Generate mock dependencies for a scan
function generateMockDependencies(scanId: number): Dependency[] {
  const templates = [
    // Critical vulnerabilities
    {
      package_name: 'lodash',
      version: '4.17.15',
      ecosystem: 'npm',
      is_vulnerable: true,
      cve_count: 2,
      highest_severity: 'HIGH',
      type: 'direct' as const,
      license: 'MIT',
      cves: [
        {
          cve_id: 'CVE-2021-23337',
          severity: 'HIGH',
          cvss_score: 7.4,
          description: 'Command injection vulnerability in lodash allows attackers to execute arbitrary commands.',
          published_date: '2021-02-15T00:00:00Z',
          vendor: 'lodash',
          product: 'lodash',
          affected_version: '<4.17.21',
        },
      ],
      usage: {
        isUsed: true,
        impactScore: 'HIGH' as const,
        locations: [
          {
            file: 'src/utils/helpers.js',
            line: 15,
            snippet: "import { merge } from 'lodash';",
          },
          {
            file: 'src/services/data-processor.js',
            line: 42,
            snippet: 'const result = _.merge(obj1, obj2);',
          },
        ],
      },
    },
    {
      package_name: 'axios',
      version: '0.21.0',
      ecosystem: 'npm',
      is_vulnerable: true,
      cve_count: 1,
      highest_severity: 'MEDIUM',
      type: 'direct' as const,
      license: 'MIT',
      cves: [
        {
          cve_id: 'CVE-2021-3749',
          severity: 'MEDIUM',
          cvss_score: 6.5,
          description: 'Improper input validation in axios could lead to SSRF attacks.',
          published_date: '2021-08-31T00:00:00Z',
        },
      ],
      usage: {
        isUsed: true,
        impactScore: 'MEDIUM' as const,
        locations: [
          {
            file: 'src/api/client.ts',
            line: 8,
            snippet: "import axios from 'axios';",
          },
        ],
      },
    },
    // Safe dependencies
    {
      package_name: 'react',
      version: '18.2.0',
      ecosystem: 'npm',
      is_vulnerable: false,
      cve_count: 0,
      type: 'direct' as const,
      license: 'MIT',
      cves: [],
    },
    {
      package_name: 'next',
      version: '14.0.4',
      ecosystem: 'npm',
      is_vulnerable: false,
      cve_count: 0,
      type: 'direct' as const,
      license: 'MIT',
      cves: [],
    },
    {
      package_name: 'typescript',
      version: '5.3.3',
      ecosystem: 'npm',
      is_vulnerable: false,
      cve_count: 0,
      type: 'dev' as const,
      license: 'Apache-2.0',
      cves: [],
    },
    // Transitive dependencies
    {
      package_name: 'minimist',
      version: '1.2.5',
      ecosystem: 'npm',
      is_vulnerable: true,
      cve_count: 1,
      highest_severity: 'CRITICAL',
      type: 'transitive' as const,
      license: 'MIT',
      cves: [
        {
          cve_id: 'CVE-2021-44906',
          severity: 'CRITICAL',
          cvss_score: 9.8,
          description: 'Prototype pollution in minimist allows attackers to modify object prototypes.',
          published_date: '2022-03-17T00:00:00Z',
        },
      ],
      usage: {
        isUsed: false,
        impactScore: 'NONE' as const,
        locations: [],
      },
    },
    {
      package_name: 'express',
      version: '4.18.2',
      ecosystem: 'npm',
      is_vulnerable: false,
      cve_count: 0,
      type: 'direct' as const,
      license: 'MIT',
      cves: [],
      usage: {
        isUsed: true,
        impactScore: 'HIGH' as const,
        locations: [
          {
            file: 'server/index.js',
            line: 3,
            snippet: "const express = require('express');",
          },
        ],
      },
    },
    {
      package_name: 'jsonwebtoken',
      version: '8.5.1',
      ecosystem: 'npm',
      is_vulnerable: true,
      cve_count: 1,
      highest_severity: 'HIGH',
      type: 'direct' as const,
      license: 'MIT',
      cves: [
        {
          cve_id: 'CVE-2022-23529',
          severity: 'HIGH',
          cvss_score: 7.5,
          description: 'Improper token verification could allow authentication bypass.',
          published_date: '2022-12-21T00:00:00Z',
        },
      ],
      usage: {
        isUsed: true,
        impactScore: 'HIGH' as const,
        locations: [
          {
            file: 'src/middleware/auth.js',
            line: 12,
            snippet: 'const token = jwt.sign(payload, secret);',
          },
        ],
      },
    },
  ]

  // Generate different dependency sets based on scan ID
  if (scanId === 1) {
    // Vulnerable app - use most templates
    return templates.map((t, idx) => ({ ...t, id: idx + 1 }))
  } else if (scanId === 2) {
    // Production - mostly safe
    return templates
      .filter((t) => !t.is_vulnerable || t.cve_count <= 1)
      .map((t, idx) => ({ ...t, id: idx + 1 }))
  } else {
    // Legacy - all dependencies
    return [...templates, ...templates.map((t) => ({ ...t, package_name: t.package_name + '-extra' }))]
      .map((t, idx) => ({ ...t, id: idx + 1 }))
  }
}

export const mockAPI = {
  // Get dashboard statistics
  async getStats(): Promise<Stats> {
    await simulateDelay()
    const scans = generateMockScans()

    return {
      total_scans: scans.length,
      total_dependencies_scanned: scans.reduce((sum, s) => sum + s.total_dependencies, 0),
      total_vulnerabilities_found: scans.reduce((sum, s) => sum + s.total_cves, 0),
      critical_vulnerabilities: scans.reduce((sum, s) => sum + s.severity_counts.critical, 0),
      recent_scans: scans,
    }
  },

  // Get list of scans
  async getScans(page: number = 1, perPage: number = 10): Promise<ScanListResponse> {
    await simulateDelay()
    const scans = generateMockScans()

    return {
      scans,
      total: scans.length,
      page,
      per_page: perPage,
      pages: Math.ceil(scans.length / perPage),
    }
  },

  // Get scan detail
  async getScan(id: number): Promise<ScanDetail> {
    await simulateDelay()
    const scans = generateMockScans()
    const scan = scans.find((s) => s.id === id)

    if (!scan) {
      throw new Error('Scan not found')
    }

    const dependencies = generateMockDependencies(id)

    return {
      ...scan,
      dependencies,
    }
  },

  // Upload scan (creates new mock scan)
  async uploadScan(file: File): Promise<ScanDetail> {
    await simulateDelay(1500) // Longer delay for upload simulation

    const newId = 4
    const newScan: ScanDetail = {
      id: newId,
      file_name: file.name,
      file_type: file.name.endsWith('.json') ? 'npm' : 'pip',
      scan_date: new Date().toISOString(),
      total_dependencies: 28,
      vulnerable_dependencies: 5,
      total_cves: 7,
      severity_counts: {
        critical: 1,
        high: 2,
        medium: 3,
        low: 1,
      },
      dependencies: generateMockDependencies(1).slice(0, 5),
    }

    return newScan
  },

  // Delete scan
  async deleteScan(id: number): Promise<void> {
    await simulateDelay()
    console.log(`[MOCK API] Deleted scan ${id}`)
  },

  // Health check
  async healthCheck(): Promise<{ status: string; version: string }> {
    return {
      status: 'ok (mock)',
      version: '1.0.0-mock',
    }
  },
}

// Simulate network delay
function simulateDelay(ms: number = 300): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms))
}

// Set demo mode flag globally
if (typeof window !== 'undefined') {
  ;(window as any).__DEMO_MODE__ = true
}
