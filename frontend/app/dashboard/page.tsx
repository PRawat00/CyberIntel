"use client"

import Link from "next/link"
import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/contexts/auth-context"
import { useStats } from "@/hooks/use-scans"
import { Button } from "@/components/ui/button"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { StatsCard } from "@/components/dashboard/stats-card"
import { SeverityChart } from "@/components/charts/severity-chart"
import { RecentScans } from "@/components/dashboard/recent-scans"
import {
  Upload,
  FileSearch,
  Shield,
  AlertTriangle,
  TrendingUp,
} from "lucide-react"

export default function DashboardPage() {
  const { user, loading } = useAuth()
  const router = useRouter()
  const { data: stats, isLoading, error } = useStats()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-8">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-96" />
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Skeleton className="h-[400px]" />
            <Skeleton className="h-[400px]" />
          </div>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!user) {
    router.push('/auth/login')
    return null
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load dashboard statistics. Please ensure the API is running.
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-8">
          <div>
            <Skeleton className="h-10 w-64 mb-2" />
            <Skeleton className="h-6 w-96" />
          </div>

          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
            {[...Array(4)].map((_, i) => (
              <Skeleton key={i} className="h-32" />
            ))}
          </div>

          <div className="grid gap-6 md:grid-cols-2">
            <Skeleton className="h-[400px]" />
            <Skeleton className="h-[400px]" />
          </div>
        </div>
      </div>
    )
  }

  if (!stats) {
    return null
  }

  // Calculate total severity counts from recent scans
  const totalSeverityCounts = stats.recent_scans.reduce(
    (acc, scan) => ({
      critical: acc.critical + scan.severity_counts.critical,
      high: acc.high + scan.severity_counts.high,
      medium: acc.medium + scan.severity_counts.medium,
      low: acc.low + scan.severity_counts.low,
    }),
    { critical: 0, high: 0, medium: 0, low: 0 }
  )

  return (
    <div className="container mx-auto py-8 px-4">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between mb-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight mb-2">Dashboard</h1>
          <p className="text-muted-foreground">
            Overview of your dependency security scans
          </p>
        </div>
        <Button asChild className="mt-4 md:mt-0">
          <Link href="/upload">
            <Upload className="mr-2 h-4 w-4" />
            New Scan
          </Link>
        </Button>
      </div>

      {/* Stats Cards */}
      <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4 mb-8">
        <StatsCard
          title="Total Scans"
          value={stats.total_scans}
          description="All-time scans"
          icon={FileSearch}
        />
        <StatsCard
          title="Dependencies Scanned"
          value={stats.total_dependencies_scanned.toLocaleString()}
          description="Across all projects"
          icon={TrendingUp}
        />
        <StatsCard
          title="Vulnerabilities Found"
          value={stats.total_vulnerabilities_found}
          description={
            stats.total_vulnerabilities_found > 0
              ? "Needs attention"
              : "All clear"
          }
          icon={stats.total_vulnerabilities_found > 0 ? AlertTriangle : Shield}
        />
        <StatsCard
          title="Critical Issues"
          value={stats.critical_vulnerabilities}
          description={
            stats.critical_vulnerabilities > 0
              ? "Immediate action required"
              : "No critical issues"
          }
          icon={AlertTriangle}
        />
      </div>

      {/* Charts and Recent Scans */}
      <div className="grid gap-6 md:grid-cols-2 mb-8">
        <SeverityChart severityData={totalSeverityCounts} />
        <RecentScans scans={stats.recent_scans.slice(0, 5)} />
      </div>

      {/* Empty State */}
      {stats.total_scans === 0 && (
        <div className="text-center py-12">
          <Shield className="h-16 w-16 mx-auto text-muted-foreground mb-4" />
          <h2 className="text-2xl font-semibold mb-2">No scans yet</h2>
          <p className="text-muted-foreground mb-6">
            Upload your first dependency file to start scanning for vulnerabilities
          </p>
          <Button asChild size="lg">
            <Link href="/upload">
              <Upload className="mr-2 h-5 w-5" />
              Upload First File
            </Link>
          </Button>
        </div>
      )}
    </div>
  )
}
