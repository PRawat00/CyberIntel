"use client"

import { useState, useEffect } from "react"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { useScan } from "@/hooks/use-scans"
import { NetworkGraph } from "@/components/graph/NetworkGraph"
import { VulnerabilityTable } from "@/components/scan/vulnerability-table"
import { NodeDetailsPanel } from "@/components/graph/node-details-panel"
import { transformToGraphData } from "@/components/graph/graph-utils"
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Skeleton } from "@/components/ui/skeleton"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Network, Table2, Upload, AlertCircle } from "lucide-react"
import type { GraphNode } from "@/lib/types"

export default function DependenciesPage() {
  const { selectedScanId } = useNavigationState()
  const { data: scan, isLoading, error } = useScan(selectedScanId || 0)

  const [viewMode, setViewMode] = useState<"graph" | "table">("graph")
  const [selectedNodeIds, setSelectedNodeIds] = useState<string[]>([])
  const [clickPosition, setClickPosition] = useState<{ x: number; y: number } | undefined>()

  // Reset selection when scan changes
  useEffect(() => {
    setSelectedNodeIds([])
    setClickPosition(undefined)
  }, [selectedScanId])

  // Handle node selection from graph
  const handleNodeClick = (node: GraphNode, isMultiSelect: boolean, position?: { x: number; y: number }) => {
    if (isMultiSelect) {
      setSelectedNodeIds((prev) =>
        prev.includes(node.id) ? prev.filter((id) => id !== node.id) : [...prev, node.id]
      )
    } else {
      // Toggle logic: if node is already selected as the only selection, deselect it
      setSelectedNodeIds((prev) =>
        prev.includes(node.id) && prev.length === 1 ? [] : [node.id]
      )
    }
    if (position) {
      setClickPosition(position)
    }
  }

  // Handle table row click - show same popup as graph node
  const handleTableRowClick = (dependency: any) => {
    const node = graphData.nodes.find((n) => n.id === dependency.package_name)
    if (node) {
      setSelectedNodeIds([node.id])
      setClickPosition(undefined) // Use default positioning
    }
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

  // Get selected nodes for details panel
  const selectedNodes = graphData.nodes.filter((node) => selectedNodeIds.includes(node.id))

  return (
    <>
      <div className="container mx-auto py-6 px-4">
      {/* Header */}
      <div className="flex items-center justify-between mb-6">
        <div>
          <h1 className="text-3xl font-bold text-slate-100">{scan.file_name}</h1>
          <p className="text-slate-400 mt-1">
            {scan.total_dependencies} dependencies • {scan.vulnerable_dependencies} vulnerable
          </p>
        </div>

        <div className="flex items-center gap-4">
          {/* Severity Badges */}
          <div className="flex gap-2">
            {scan.severity_counts.critical > 0 && (
              <Badge className="bg-[hsl(var(--severity-critical))] text-white">
                {scan.severity_counts.critical} Critical
              </Badge>
            )}
            {scan.severity_counts.high > 0 && (
              <Badge className="bg-[hsl(var(--severity-high))] text-white">
                {scan.severity_counts.high} High
              </Badge>
            )}
            {scan.severity_counts.medium > 0 && (
              <Badge className="bg-[hsl(var(--severity-medium))] text-white">
                {scan.severity_counts.medium} Medium
              </Badge>
            )}
            {scan.severity_counts.low > 0 && (
              <Badge className="bg-[hsl(var(--severity-low))] text-white">
                {scan.severity_counts.low} Low
              </Badge>
            )}
          </div>
        </div>
      </div>

      {/* View Toggle Tabs */}
      <Tabs value={viewMode} onValueChange={(value) => setViewMode(value as "graph" | "table")}>
        <TabsList className="grid w-full max-w-md grid-cols-2 mb-6">
          <TabsTrigger value="graph" className="flex items-center gap-2">
            <Network className="h-4 w-4" />
            Graph View
          </TabsTrigger>
          <TabsTrigger value="table" className="flex items-center gap-2">
            <Table2 className="h-4 w-4" />
            Table View
          </TabsTrigger>
        </TabsList>

        {/* Graph View */}
        <TabsContent value="graph" className="mt-0">
          <Card>
            <CardHeader>
              <CardTitle>Dependency Graph</CardTitle>
              <CardDescription>
                Visualize dependencies and vulnerabilities. Click nodes to inspect details.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="w-full h-[700px] border border-dark-border rounded-lg bg-dark-bg/50">
                <NetworkGraph
                  nodes={graphData.nodes}
                  links={graphData.links}
                  selectedNodeIds={selectedNodeIds}
                  onNodeClick={handleNodeClick}
                />
              </div>

              {selectedNodeIds.length > 0 && (
                <div className="mt-4 p-4 border border-brand-500/30 rounded-lg bg-brand-500/5">
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
            </CardContent>
          </Card>
        </TabsContent>

        {/* Table View */}
        <TabsContent value="table" className="mt-0">
          <VulnerabilityTable
            dependencies={scan.dependencies}
            scanId={scan.id}
            onRowClick={handleTableRowClick}
          />
        </TabsContent>
      </Tabs>
    </div>

    {/* Node Details Panel */}
    {selectedNodes.length > 0 && (
      <NodeDetailsPanel
        nodes={selectedNodes}
        onClose={() => {
          setSelectedNodeIds([])
          setClickPosition(undefined)
        }}
        position={clickPosition}
        chatSidebarOpen={true}
      />
    )}
  </>
  )
}
