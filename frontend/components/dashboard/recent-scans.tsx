"use client"

import Link from "next/link"
import { formatDistanceToNow } from "date-fns"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { FileText, AlertTriangle, CheckCircle2, ArrowRight } from "lucide-react"
import type { ScanSummary } from "@/lib/types"

interface RecentScansProps {
  scans: ScanSummary[]
}

export function RecentScans({ scans }: RecentScansProps) {
  if (scans.length === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Recent Scans</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center py-8">
          <FileText className="h-12 w-12 text-muted-foreground mb-4" />
          <p className="text-muted-foreground text-center">No scans yet</p>
          <Button asChild className="mt-4">
            <Link href="/upload">Upload your first file</Link>
          </Button>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between">
        <CardTitle>Recent Scans</CardTitle>
        <Button variant="ghost" size="sm" asChild>
          <Link href="/dashboard/scans">
            View all
            <ArrowRight className="ml-2 h-4 w-4" />
          </Link>
        </Button>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {scans.map((scan) => (
            <Link
              key={scan.id}
              href={`/dashboard/scans/${scan.id}`}
              className="block group"
            >
              <div className="flex items-start justify-between p-4 rounded-lg border hover:border-primary transition-colors">
                <div className="flex items-start gap-3 flex-1">
                  <div className="mt-1">
                    {scan.vulnerable_dependencies > 0 ? (
                      <AlertTriangle className="h-5 w-5 text-orange-500" />
                    ) : (
                      <CheckCircle2 className="h-5 w-5 text-green-500" />
                    )}
                  </div>
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1">
                      <p className="font-medium truncate">{scan.file_name}</p>
                      <Badge variant="outline" className="text-xs">
                        {scan.file_type}
                      </Badge>
                    </div>
                    <div className="flex items-center gap-4 text-sm text-muted-foreground">
                      <span>
                        {scan.total_dependencies} {scan.total_dependencies === 1 ? "dependency" : "dependencies"}
                      </span>
                      {scan.vulnerable_dependencies > 0 && (
                        <span className="text-orange-600 dark:text-orange-400 font-medium">
                          {scan.vulnerable_dependencies} vulnerable
                        </span>
                      )}
                      <span>
                        {formatDistanceToNow(new Date(scan.scan_date), {
                          addSuffix: true,
                        })}
                      </span>
                    </div>
                  </div>
                </div>

                {scan.total_cves > 0 && (
                  <div className="flex gap-1 ml-2">
                    {scan.severity_counts.critical > 0 && (
                      <Badge className="bg-[hsl(var(--severity-critical))] text-white">
                        {scan.severity_counts.critical}
                      </Badge>
                    )}
                    {scan.severity_counts.high > 0 && (
                      <Badge className="bg-[hsl(var(--severity-high))] text-white">
                        {scan.severity_counts.high}
                      </Badge>
                    )}
                    {scan.severity_counts.medium > 0 && (
                      <Badge className="bg-[hsl(var(--severity-medium))] text-white">
                        {scan.severity_counts.medium}
                      </Badge>
                    )}
                  </div>
                )}
              </div>
            </Link>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
