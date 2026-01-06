"use client"

import { useState, useEffect } from "react"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { useScan } from "@/hooks/use-scans"
import { NetworkGraph } from "@/components/graph/NetworkGraph"
import { VulnerabilityTable } from "@/components/scan/vulnerability-table"
import { CveDetailsDialog } from "@/components/scan/cve-details-dialog"
import { transformToGraphData } from "@/components/graph/graph-utils"
import { logger } from "@/lib/logger"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Button } from "@/components/ui/button"
import { Network, Table2, Upload, AlertCircle } from "lucide-react"
import { cn } from "@/lib/utils"
import type { GraphNode, Dependency } from "@/lib/types"

export default function DependenciesPage() {
  const { selectedScanId } = useNavigationState()

  // Debug logging
  logger.log('[DEPENDENCIES PAGE] Render:', {
    selectedScanId,
    timestamp: new Date().toISOString()
  })

  const { data: scan, isLoading, error } = useScan(selectedScanId || 0)

  logger.log('[DEPENDENCIES PAGE] Query state:', {
    selectedScanId,
    isLoading,
    hasScan: !!scan,
    error: error?.message
  })

  const [viewMode, setViewMode] = useState<"graph" | "table">("graph")
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([])
  const [selectedDependency, setSelectedDependency] = useState<Dependency | null>(null)
  const [dialogOpen, setDialogOpen] = useState(false)

  // Reset selection when scan changes
  useEffect(() => {
    setSelectedNodeIds([])
  }, [selectedScanId])

  // Handle node selection from graph - open CVE details dialog
  const handleNodeClick = (node: GraphNode, isMultiSelect: boolean) => {
    // Open CVE details dialog with the node's dependency data
    setSelectedDependency(node.data)
    setDialogOpen(true)

    // Keep node highlighted in graph for visual feedback
    if (isMultiSelect) {
      setSelectedNodeIds((prev) =>
        prev.includes(node.id) ? prev.filter((id) => id !== node.id) : [...prev, node.id]
      )
    } else {
      setSelectedNodeIds([node.id])
    }
  }

  // Handle table row click - open CVE details dialog
  const handleTableRowClick = (dependency: Dependency) => {
    setSelectedDependency(dependency)
    setDialogOpen(true)
  }

  // Empty state - no scan selected
  if (!selectedScanId) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="flex items-center justify-center min-h-[calc(100vh-200px)]">
          <Card className="max-w-md w-full">
            <CardContent className="flex flex-col items-center justify-center py-12">
              <Upload className="h-16 w-16 text-muted-foreground mb-4" />
              <h3 className="text-xl font-semibold mb-2">No scan selected</h3>
              <p className="text-muted-foreground text-center mb-4">
                Upload a dependency file or select a scan from the sidebar to get started
              </p>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  // Loading state
  if (isLoading) {
    return (
      <div className="container mx-auto py-8 px-4">
        <div className="space-y-4">
          <Skeleton className="h-12 w-64" />
          <Skeleton className="h-[600px] w-full" />
        </div>
      </div>
    )
  }

  // Error state
  if (error || !scan) {
    return (
      <div className="container mx-auto py-8 px-4">
        <Alert variant="destructive">
          <AlertCircle className="h-4 w-4" />
          <AlertDescription>
            {error instanceof Error ? error.message : "Failed to load scan"}
          </AlertDescription>
        </Alert>
      </div>
    )
  }

  // Transform scan data for graph
  const graphData = transformToGraphData(scan.dependencies, scan.file_name)

  logger.log('[DEPENDENCIES PAGE] Rendering graph:', {
    scanId: scan.id,
    fileName: scan.file_name,
    nodesCount: graphData.nodes.length,
    linksCount: graphData.links.length,
    viewMode
  })

  return (
    <>
      <div className="h-full w-full flex flex-col p-4">
        {/* Content Card - fills entire space */}
        <Card className="h-full flex flex-col">
          <CardHeader className="flex-none">
            <div className="flex items-center justify-between gap-4">
              <div className="flex-1 min-w-0">
                <CardTitle className="text-2xl">{scan.file_name}</CardTitle>
                <div className="flex items-center gap-3 mt-2 flex-wrap">
                  <p className="text-sm text-slate-300">
                    {scan.total_dependencies} dependencies • {scan.vulnerable_dependencies} vulnerable
                  </p>
                  {/* Severity Badges */}
                  <div className="flex gap-1.5">
                    {scan.severity_counts.critical > 0 && (
                      <Badge className="bg-[hsl(var(--severity-critical))] text-white text-xs">
                        {scan.severity_counts.critical} Critical
                      </Badge>
                    )}
                    {scan.severity_counts.high > 0 && (
                      <Badge className="bg-[hsl(var(--severity-high))] text-white text-xs">
                        {scan.severity_counts.high} High
                      </Badge>
                    )}
                    {scan.severity_counts.medium > 0 && (
                      <Badge className="bg-[hsl(var(--severity-medium))] text-white text-xs">
                        {scan.severity_counts.medium} Medium
                      </Badge>
                    )}
                    {scan.severity_counts.low > 0 && (
                      <Badge className="bg-[hsl(var(--severity-low))] text-white text-xs">
                        {scan.severity_counts.low} Low
                      </Badge>
                    )}
                  </div>
                </div>
                <CardDescription className="mt-2 text-slate-400">
                  {viewMode === "graph"
                    ? "Visualize dependencies and vulnerabilities. Click nodes to inspect details."
                    : "View all dependencies and their vulnerabilities in a table format."}
                </CardDescription>
              </div>
              {/* View Toggle Buttons */}
              <div className="flex gap-1 bg-muted p-1 rounded-lg">
                <Button
                  variant={viewMode === "graph" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("graph")}
                  className={cn(
                    "gap-2",
                    viewMode === "graph" && "bg-background shadow-sm"
                  )}
                >
                  <Network className="h-4 w-4" />
                  Graph
                </Button>
                <Button
                  variant={viewMode === "table" ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setViewMode("table")}
                  className={cn(
                    "gap-2",
                    viewMode === "table" && "bg-background shadow-sm"
                  )}
                >
                  <Table2 className="h-4 w-4" />
                  Table
                </Button>
              </div>
            </div>
          </CardHeader>

            <CardContent className="flex-1 min-h-0 flex flex-col p-0">
              {viewMode === "graph" ? (
                <div className="relative h-[600px] border-t border-border overflow-hidden">
                  <NetworkGraph
                    nodes={graphData.nodes}
                    links={graphData.links}
                    selectedNodeIds={selectedNodeIds}
                    onNodeClick={handleNodeClick}
                  />
                  {selectedNodeIds.length > 0 && (
                    <div className="absolute bottom-4 left-6 right-6 p-4 border border-brand-500/30 rounded-lg bg-brand-500/5 backdrop-blur-sm shadow-lg">
                      <p className="text-sm text-slate-300">
                        {selectedNodeIds.length} node(s) selected •{" "}
                        <button
                          onClick={() => setSelectedNodeIds([])}
                          className="text-brand-400 hover:text-brand-300 underline"
                        >
                          Clear selection
                        </button>
                      </p>
                    </div>
                  )}
                </div>
              ) : (
                <div className="flex-1 overflow-auto">
                  <VulnerabilityTable
                    dependencies={scan.dependencies}
                    scanId={scan.id}
                    onRowClick={handleTableRowClick}
                  />
                </div>
              )}
            </CardContent>
          </Card>
      </div>

      {/* CVE Details Dialog */}
      <CveDetailsDialog
        dependency={selectedDependency}
        open={dialogOpen}
        onOpenChange={(open) => {
          setDialogOpen(open)
          // Clear node selection when dialog closes to prevent graph shifting
          if (!open) {
            setSelectedNodeIds([])
          }
        }}
      />
    </>
  )
}
