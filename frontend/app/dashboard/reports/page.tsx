'use client'

import { useState, useEffect } from 'react'
import { useScans } from '@/hooks/use-scans'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import { Alert, AlertDescription } from '@/components/ui/alert'
import { BarChart, Bar, PieChart, Pie, Cell, ResponsiveContainer, XAxis, YAxis, Tooltip, Legend } from 'recharts'
import { Shield, Scale, CheckCircle, AlertTriangle, Download, FileText } from 'lucide-react'
import type { LicenseDistribution, RiskFactor } from '@/lib/types'

export default function ReportsPage() {
  const { data: scansResponse, isLoading, error } = useScans()
  const [selectedScanId, setSelectedScanId] = useState<number | null>(null)

  // Select first scan by default
  useEffect(() => {
    if (scansResponse?.scans && scansResponse.scans.length > 0 && !selectedScanId) {
      setSelectedScanId(scansResponse.scans[0].id)
    }
  }, [scansResponse, selectedScanId])

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load scans. The API may not be running.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Skeleton className="h-10 w-64 mb-6" />
        <div className="grid gap-6 md:grid-cols-3 mb-6">
          {[...Array(3)].map((_, i) => (
            <Skeleton key={i} className="h-32" />
          ))}
        </div>
        <Skeleton className="h-[400px]" />
      </div>
    )
  }

  const scans = scansResponse?.scans || []
  const selectedScan = scans.find((s) => s.id === selectedScanId)

  // Generate mock data for demonstration
  const securityScore = selectedScan ? calculateSecurityScore(selectedScan) : 0
  const licenseRisk = selectedScan ? calculateLicenseRisk(selectedScan) : 'low'
  const policyStatus = selectedScan ? determinePolicyStatus(selectedScan) : 'passed'
  const licenseDistribution = selectedScan ? generateLicenseDistribution(selectedScan) : []
  const riskFactors = selectedScan ? generateRiskFactors(selectedScan) : []

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Security & Compliance Reports</h1>
        <p className="text-muted-foreground">
          Comprehensive analysis of license compliance, security posture, and risk assessment
        </p>
      </div>

      {/* Scan Selector */}
      {scans.length > 0 && (
        <div className="mb-6">
          <label className="text-sm font-medium mb-2 block">Select Scan</label>
          <Select
            value={selectedScanId?.toString()}
            onValueChange={(value) => setSelectedScanId(parseInt(value))}
          >
            <SelectTrigger className="w-full max-w-md">
              <SelectValue placeholder="Select a scan" />
            </SelectTrigger>
            <SelectContent>
              {scans.map((scan) => (
                <SelectItem key={scan.id} value={scan.id.toString()}>
                  {scan.file_name} - {new Date(scan.scan_date).toLocaleDateString()}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>
      )}

      {selectedScan ? (
        <>
          {/* Summary Cards */}
          <div className="grid gap-4 md:grid-cols-3 mb-6">
            {/* Security Score */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Security Score</CardTitle>
                <Shield className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="text-3xl font-bold mb-2">{securityScore}/100</div>
                <Progress value={securityScore} className="mb-2" />
                <p className="text-xs text-muted-foreground">
                  {securityScore >= 80
                    ? 'Excellent security posture'
                    : securityScore >= 60
                    ? 'Good, with room for improvement'
                    : 'Needs attention'}
                </p>
              </CardContent>
            </Card>

            {/* License Risk */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">License Risk</CardTitle>
                <Scale className="h-4 w-4 text-muted-foreground" />
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    className={
                      licenseRisk === 'low'
                        ? 'bg-green-500'
                        : licenseRisk === 'medium'
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }
                  >
                    {licenseRisk.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  Based on license compatibility analysis
                </p>
              </CardContent>
            </Card>

            {/* Policy Status */}
            <Card>
              <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                <CardTitle className="text-sm font-medium">Policy Compliance</CardTitle>
                {policyStatus === 'passed' ? (
                  <CheckCircle className="h-4 w-4 text-green-500" />
                ) : (
                  <AlertTriangle className="h-4 w-4 text-orange-500" />
                )}
              </CardHeader>
              <CardContent>
                <div className="flex items-center gap-2 mb-2">
                  <Badge
                    className={
                      policyStatus === 'passed'
                        ? 'bg-green-500'
                        : policyStatus === 'warning'
                        ? 'bg-yellow-500'
                        : 'bg-red-500'
                    }
                  >
                    {policyStatus.toUpperCase()}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground">
                  {policyStatus === 'passed'
                    ? 'All policies satisfied'
                    : 'Some policies need review'}
                </p>
              </CardContent>
            </Card>
          </div>

          {/* Charts Row */}
          <div className="grid gap-6 md:grid-cols-2 mb-6">
            {/* License Distribution */}
            <Card>
              <CardHeader>
                <CardTitle>License Distribution</CardTitle>
                <CardDescription>
                  Breakdown of licenses across dependencies
                </CardDescription>
              </CardHeader>
              <CardContent>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie
                      data={licenseDistribution as any}
                      dataKey="count"
                      nameKey="license"
                      cx="50%"
                      cy="50%"
                      outerRadius={100}
                      label={(entry: any) => `${entry.license} (${entry.percentage}%)`}
                    >
                      {licenseDistribution.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={LICENSE_COLORS[index % LICENSE_COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </CardContent>
            </Card>

            {/* Risk Factors */}
            <Card>
              <CardHeader>
                <CardTitle>Top Risk Factors</CardTitle>
                <CardDescription>
                  Primary security and compliance concerns
                </CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {riskFactors.map((factor, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                          <Badge
                            variant={
                              factor.severity === 'high'
                                ? 'destructive'
                                : factor.severity === 'medium'
                                ? 'default'
                                : 'secondary'
                            }
                          >
                            {factor.severity}
                          </Badge>
                          <span className="text-sm font-medium">{factor.title}</span>
                        </div>
                        <span className="text-sm text-muted-foreground">{factor.count}</span>
                      </div>
                      <p className="text-xs text-muted-foreground">{factor.description}</p>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Export Actions */}
          <Card>
            <CardHeader>
              <CardTitle>Export Report</CardTitle>
              <CardDescription>
                Download this report in various formats
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex flex-wrap gap-2">
                <Button variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Export PDF
                </Button>
                <Button variant="outline">
                  <Download className="mr-2 h-4 w-4" />
                  Export CSV
                </Button>
                <Button variant="outline">
                  <FileText className="mr-2 h-4 w-4" />
                  Generate Summary
                </Button>
              </div>
            </CardContent>
          </Card>
        </>
      ) : (
        <Card>
          <CardContent className="py-12 text-center">
            <p className="text-muted-foreground">No scans available. Upload a file to get started.</p>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

// Helper functions for mock data generation
function calculateSecurityScore(scan: any): number {
  const totalDeps = scan.total_dependencies
  const vulnerableDeps = scan.vulnerable_dependencies
  const criticalCount = scan.severity_counts.critical
  const highCount = scan.severity_counts.high

  let score = 100
  score -= (vulnerableDeps / totalDeps) * 40
  score -= criticalCount * 5
  score -= highCount * 2

  return Math.max(0, Math.min(100, Math.round(score)))
}

function calculateLicenseRisk(scan: any): 'low' | 'medium' | 'high' {
  const totalDeps = scan.total_dependencies
  if (totalDeps > 100) return 'medium'
  if (totalDeps > 50) return 'low'
  return 'low'
}

function determinePolicyStatus(scan: any): 'passed' | 'warning' | 'failed' {
  if (scan.severity_counts.critical > 0) return 'failed'
  if (scan.severity_counts.high > 2) return 'warning'
  return 'passed'
}

function generateLicenseDistribution(scan: any): LicenseDistribution[] {
  const totalDeps = scan.total_dependencies
  return [
    { license: 'MIT', count: Math.round(totalDeps * 0.5), percentage: 50 },
    { license: 'Apache-2.0', count: Math.round(totalDeps * 0.25), percentage: 25 },
    { license: 'ISC', count: Math.round(totalDeps * 0.15), percentage: 15 },
    { license: 'GPL-3.0', count: Math.round(totalDeps * 0.05), percentage: 5 },
    { license: 'Unknown', count: Math.round(totalDeps * 0.05), percentage: 5 },
  ]
}

function generateRiskFactors(scan: any): RiskFactor[] {
  const factors: RiskFactor[] = []

  if (scan.severity_counts.critical > 0) {
    factors.push({
      title: 'Critical Vulnerabilities',
      description: `${scan.severity_counts.critical} critical CVEs require immediate attention`,
      severity: 'high',
      count: scan.severity_counts.critical,
    })
  }

  if (scan.severity_counts.high > 0) {
    factors.push({
      title: 'High Severity Issues',
      description: `${scan.severity_counts.high} high-severity vulnerabilities detected`,
      severity: 'high',
      count: scan.severity_counts.high,
    })
  }

  if (scan.total_dependencies > 100) {
    factors.push({
      title: 'Large Dependency Footprint',
      description: 'High number of dependencies increases attack surface',
      severity: 'medium',
      count: scan.total_dependencies,
    })
  }

  if (factors.length === 0) {
    factors.push({
      title: 'No Major Risks',
      description: 'No significant security or compliance risks detected',
      severity: 'low',
      count: 0,
    })
  }

  return factors
}

const LICENSE_COLORS = ['#0ea5e9', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6']
