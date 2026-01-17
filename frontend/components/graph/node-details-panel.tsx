"use client"

import { X, AlertTriangle, CheckCircle2, Info, Code, ExternalLink } from "lucide-react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Separator } from "@/components/ui/separator"
import type { GraphNode } from "@/lib/types"
import { getNvdUrl } from "@/lib/utils"

interface NodeDetailsPanelProps {
  nodes: GraphNode[]
  onClose: () => void
  position?: { x: number; y: number }
  chatSidebarOpen: boolean
}

/**
 * Calculate optimal position for the details panel
 * Avoids chat sidebar and keeps panel within viewport
 */
function calculatePanelPosition(
  clickX: number,
  clickY: number,
  panelWidth: number,
  panelHeight: number,
  chatOpen: boolean
): React.CSSProperties {
  const CHAT_WIDTH = 380
  const MARGIN = 16
  const L2_SIDEBAR_WIDTH = 320
  const L1_SIDEBAR_WIDTH = 80

  const viewportWidth = window.innerWidth
  const viewportHeight = window.innerHeight

  // Calculate available space
  const leftSidebarWidth = L1_SIDEBAR_WIDTH + L2_SIDEBAR_WIDTH
  const chatWidth = chatOpen ? CHAT_WIDTH : 0
  const availableRight = viewportWidth - chatWidth - MARGIN
  const availableLeft = leftSidebarWidth + MARGIN

  let left: number | undefined
  let right: number | undefined
  let top: number | undefined
  let bottom: number | undefined

  // Try to position near click but avoid overlaps
  // Prefer right side if there's space, otherwise left

  // Check if panel fits on the right side of click
  if (clickX + panelWidth + MARGIN < availableRight) {
    left = Math.min(clickX + MARGIN, availableRight - panelWidth)
  } else if (clickX - panelWidth - MARGIN > availableLeft) {
    // Try left side of click
    left = Math.max(clickX - panelWidth - MARGIN, availableLeft)
  } else {
    // Center in available space if click is in middle
    const availableWidth = availableRight - availableLeft
    left = availableLeft + (availableWidth - panelWidth) / 2
  }

  // Vertical positioning
  if (clickY + panelHeight + MARGIN < viewportHeight) {
    top = clickY + MARGIN
  } else if (clickY - panelHeight - MARGIN > 0) {
    top = clickY - panelHeight - MARGIN
  } else {
    // Center vertically if doesn't fit
    top = Math.max(MARGIN, (viewportHeight - panelHeight) / 2)
  }

  return {
    position: 'fixed',
    left: `${left}px`,
    top: `${top}px`,
  }
}

export function NodeDetailsPanel({ nodes, onClose, position, chatSidebarOpen }: NodeDetailsPanelProps) {
  if (nodes.length === 0) return null

  // Calculate dynamic positioning if position is provided
  const panelStyle = position
    ? calculatePanelPosition(position.x, position.y, 384, 600, chatSidebarOpen) // 384px = w-96
    : { position: 'fixed' as const, right: '1rem', bottom: '1rem' }

  // If multiple nodes selected, show summary
  if (nodes.length > 1) {
    const totalVulns = nodes.reduce(
      (sum, node) => sum + (node.data.cves?.length || 0),
      0
    )

    return (
      <Card className="w-96 max-h-[600px] shadow-xl z-50 border-2" style={panelStyle}>
        <CardHeader className="pb-3">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg">Multiple Nodes Selected</CardTitle>
            <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
              <X className="h-4 w-4" />
            </Button>
          </div>
          <CardDescription>{nodes.length} dependencies selected</CardDescription>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div>
              <p className="text-sm text-muted-foreground mb-2">Total Vulnerabilities</p>
              <p className="text-2xl font-bold">{totalVulns}</p>
            </div>
            <ScrollArea className="h-[200px]">
              <div className="space-y-2">
                {nodes.map((node) => (
                  <div
                    key={node.id}
                    className="p-2 rounded border border-dark-border bg-dark-surface"
                  >
                    <p className="text-sm font-medium truncate">{node.id}</p>
                    <p className="text-xs text-muted-foreground">
                      {node.data.cves?.length || 0} vulnerabilities
                    </p>
                  </div>
                ))}
              </div>
            </ScrollArea>
          </div>
        </CardContent>
      </Card>
    )
  }

  // Single node selected - show detailed view
  const node = nodes[0]
  const { data } = node
  const hasVulnerabilities = data.cves && data.cves.length > 0

  // Calculate positioning for single node panel
  const singleNodeStyle = position
    ? calculatePanelPosition(position.x, position.y, 450, 700, chatSidebarOpen) // 450px width, 700px height
    : { position: 'fixed' as const, right: '1rem', bottom: '1rem' }

  return (
    <Card className="w-[450px] max-h-[700px] shadow-xl z-50 border-2" style={singleNodeStyle}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            {hasVulnerabilities ? (
              <AlertTriangle className="h-5 w-5 text-orange-500" />
            ) : (
              <CheckCircle2 className="h-5 w-5 text-green-500" />
            )}
            <CardTitle className="text-lg truncate">{node.id}</CardTitle>
          </div>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8">
            <X className="h-4 w-4" />
          </Button>
        </div>
        <CardDescription className="flex items-center gap-2">
          {data.version && <Badge variant="outline">v{data.version}</Badge>}
          {data.type && (
            <Badge variant="secondary" className="capitalize">
              {data.type}
            </Badge>
          )}
        </CardDescription>
      </CardHeader>

      <ScrollArea className="h-[600px]">
        <CardContent className="space-y-4">
          <Separator />

          {/* Vulnerabilities */}
          <div>
            <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
              <AlertTriangle className="h-4 w-4" />
              Vulnerabilities
              {hasVulnerabilities && (
                <Badge variant="destructive">{data.cves.length}</Badge>
              )}
            </h4>

            {!hasVulnerabilities ? (
              <div className="flex items-center gap-2 p-3 rounded bg-green-500/10 border border-green-500/20">
                <CheckCircle2 className="h-4 w-4 text-green-500" />
                <p className="text-sm text-green-600 dark:text-green-400">
                  No known vulnerabilities
                </p>
              </div>
            ) : (
              <div className="space-y-3">
                {data.cves.map((cve, index) => (
                  <div
                    key={index}
                    className="p-3 rounded border border-dark-border bg-dark-surface"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <code className="text-xs font-mono text-brand-400">{cve.cve_id}</code>
                        <Badge
                          variant={
                            cve.severity === "CRITICAL"
                              ? "destructive"
                              : cve.severity === "HIGH"
                              ? "destructive"
                              : "secondary"
                          }
                          className="text-xs"
                        >
                          {cve.severity}
                        </Badge>
                      </div>
                      <Button variant="ghost" size="sm" className="h-6 px-2" asChild>
                        <a
                          href={getNvdUrl(cve.cve_id)}
                          target="_blank"
                          rel="noopener noreferrer"
                        >
                          <ExternalLink className="h-3 w-3" />
                        </a>
                      </Button>
                    </div>
                    <p className="text-xs text-muted-foreground mb-2">{cve.description}</p>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* Code Usage */}
          {data.usage && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-semibold mb-3 flex items-center gap-2">
                  <Code className="h-4 w-4" />
                  Code Impact
                  <Badge
                    variant={
                      data.usage.impactScore === "HIGH"
                        ? "destructive"
                        : data.usage.impactScore === "MEDIUM"
                        ? "default"
                        : "secondary"
                    }
                  >
                    {data.usage.impactScore}
                  </Badge>
                </h4>

                {data.usage.isUsed ? (
                  <div className="space-y-2">
                    <p className="text-xs text-muted-foreground mb-2">
                      Found in {data.usage.locations.length} location(s):
                    </p>
                    {data.usage.locations.map((location, index) => (
                      <div
                        key={index}
                        className="p-2 rounded border border-dark-border bg-dark-bg/50"
                      >
                        <div className="flex items-center gap-2 mb-1">
                          <code className="text-xs font-mono text-brand-400">
                            {location.file}
                          </code>
                          <Badge variant="outline" className="text-xs">
                            Line {location.line}
                          </Badge>
                        </div>
                        <pre className="text-xs text-muted-foreground overflow-x-auto">
                          <code>{location.snippet}</code>
                        </pre>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">Not actively used in code</p>
                )}
              </div>
            </>
          )}

          {/* License */}
          {data.license && (
            <>
              <Separator />
              <div>
                <h4 className="text-sm font-semibold mb-2">License</h4>
                <Badge variant="outline">{data.license}</Badge>
              </div>
            </>
          )}
        </CardContent>
      </ScrollArea>
    </Card>
  )
}
