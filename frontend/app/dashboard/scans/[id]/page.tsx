"use client"

import { use, useState, useEffect } from "react"
import { useRouter } from "next/navigation"
import { formatDistanceToNow } from "date-fns"
import { useScan, useDeleteScan } from "@/hooks/use-scans"
import { useDependencySelection } from "@/hooks/use-dependency-selection"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { VulnerabilityTable } from "@/components/scan/vulnerability-table"
import { SeverityBreakdown } from "@/components/scan/severity-breakdown"
import { CveDetailsDialog } from "@/components/scan/cve-details-dialog"
import { NetworkGraph } from "@/components/graph/NetworkGraph"
import { transformToGraphData } from "@/components/graph/graph-utils"
import {
  ArrowLeft,
  Download,
  Trash2,
  FileText,
  Shield,
  AlertTriangle,
  CheckCircle2,
} from "lucide-react"
import type { Dependency, GraphNode } from "@/lib/types"

export default function ScanDetailPage({
  params,
}: {
  params: Promise<{ id: string }>
}) {
  const resolvedParams = use(params)
  const scanId = parseInt(resolvedParams.id)
  const router = useRouter()
  const { data: scan, isLoading, error } = useScan(scanId)
  const deleteMutation = useDeleteScan()
  const [selectedDependency, setSelectedDependency] = useState<Dependency | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([])

  // Clear checkbox selections when entering this page
  useEffect(() => {
    useDependencySelection.getState().clearSelection()
  }, [scanId])

  const handleRowClick = (dependency: Dependency) => {
    setSelectedDependency(dependency)
    setDialogOpen(true)
  }

  const handleNodeClick = (node: GraphNode, isMultiSelect: boolean) => {
    setSelectedDependency(node.data)
    setDialogOpen(true)

    if (isMultiSelect) {
      setSelectedNodeIds((prev) =>
        prev.includes(node.id)
          ? prev.filter((id) => id !== node.id)
          : [...prev, node.id]
      )
    } else {
      setSelectedNodeIds([node.id])
    }
  }

  const handleDelete = async () => {
    if (!confirm("Are you sure you want to delete this scan?")) return

    try {
      await deleteMutation.mutateAsync(scanId)
      router.push("/dashboard")
    } catch (error) {
      alert("Failed to delete scan")
    }
  }

  const handleExport = (format: "json" | "csv" | "html") => {
    window.open(
      `${process.env.NEXT_PUBLIC_API_URL}/api/scans/${scanId}/export?format=${format}`,
      "_blank"
    )
  }

  if (error) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert variant="destructive">
          <AlertDescription>
            Failed to load scan results. The scan may not exist or the API is not running.
          </AlertDescription>
        </Alert>
        <Button onClick={() => router.push("/dashboard")} className="mt-4">
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>
      </div>
    )
  }

  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Skeleton className="h-10 w-32 mb-6" />
        <div className="space-y-6">
          <Skeleton className="h-32" />
          <div className="grid gap-6 md:grid-cols-3">
            {[...Array(3)].map((_, i) => (
              <Skeleton key={i} className="h-24" />
            ))}
          </div>
          <Skeleton className="h-[400px]" />
        </div>
      </div>
    )
  }

  if (!scan) {
    return null
  }

  // Transform dependencies to graph data
  const graphData = transformToGraphData(scan.dependencies, scan.file_name)

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <Button
          variant="ghost"
          onClick={() => router.push("/dashboard")}
          className="mb-4"
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
          <div>
            <div className="flex items-center gap-3 mb-2">
              <h1 className="text-3xl font-bold">{scan.file_name}</h1>
              <Badge variant="outline" className="capitalize">
                {scan.file_type}
              </Badge>
            </div>
            <p className="text-muted-foreground">
              Scanned {formatDistanceToNow(new Date(scan.scan_date), { addSuffix: true })}
            </p>
          </div>

          <div className="flex gap-2">
            <Button
              variant="outline"
              onClick={() => handleExport("json")}
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              JSON
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport("csv")}
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              CSV
            </Button>
            <Button
              variant="outline"
              onClick={() => handleExport("html")}
              size="sm"
            >
              <Download className="mr-2 h-4 w-4" />
              HTML
            </Button>
            <Button
              variant="destructive"
              onClick={handleDelete}
              disabled={deleteMutation.isPending}
              size="sm"
            >
              <Trash2 className="mr-2 h-4 w-4" />
              Delete
            </Button>
          </div>
        </div>
      </div>

      {/* Summary Stats */}
      <div className="grid gap-4 md:grid-cols-4 mb-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total Dependencies
            </CardTitle>
            <FileText className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scan.total_dependencies}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Vulnerable
            </CardTitle>
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-orange-600 dark:text-orange-400">
              {scan.vulnerable_dependencies}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Safe
            </CardTitle>
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-green-600 dark:text-green-400">
              {scan.total_dependencies - scan.vulnerable_dependencies}
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
            <CardTitle className="text-sm font-medium">
              Total CVEs
            </CardTitle>
            <Shield className="h-4 w-4 text-muted-foreground" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{scan.total_cves}</div>
          </CardContent>
        </Card>
      </div>

      {/* Severity Breakdown & Vulnerabilities */}
      <div className="grid gap-6 md:grid-cols-3 mb-6">
        <div className="md:col-span-1">
          <SeverityBreakdown
            severityData={scan.severity_counts}
            totalCves={scan.total_cves}
          />
        </div>

        <div className="md:col-span-2">
          <Card>
            <CardHeader>
              <CardTitle>Quick Stats</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Critical</p>
                  <p className="text-2xl font-bold text-[hsl(var(--severity-critical))]">
                    {scan.severity_counts.critical}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">High</p>
                  <p className="text-2xl font-bold text-[hsl(var(--severity-high))]">
                    {scan.severity_counts.high}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Medium</p>
                  <p className="text-2xl font-bold text-[hsl(var(--severity-medium))]">
                    {scan.severity_counts.medium}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Low</p>
                  <p className="text-2xl font-bold text-[hsl(var(--severity-low))]">
                    {scan.severity_counts.low}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>

      {/* Dependencies - Table & Graph View */}
      <Card>
        <CardHeader>
          <CardTitle>Dependencies ({scan.dependencies.length})</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="table" className="w-full">
            <TabsList className="grid w-full max-w-md grid-cols-2 mb-4">
              <TabsTrigger value="table">Table View</TabsTrigger>
              <TabsTrigger value="graph">Graph View</TabsTrigger>
            </TabsList>

            <TabsContent value="table" className="mt-0">
              <VulnerabilityTable
                dependencies={scan.dependencies}
                scanId={scan.id}
                onRowClick={handleRowClick}
              />
            </TabsContent>

            <TabsContent value="graph" className="mt-0">
              <div className="w-full h-[600px]">
                <NetworkGraph
                  nodes={graphData.nodes}
                  links={graphData.links}
                  selectedNodeIds={selectedNodeIds}
                  onNodeClick={handleNodeClick}
                />
              </div>
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>

      {/* CVE Details Dialog */}
      <CveDetailsDialog
        dependency={selectedDependency}
        open={dialogOpen}
        onOpenChange={setDialogOpen}
      />
    </div>
  )
}
