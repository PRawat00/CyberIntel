"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"
import type { SeverityCount } from "@/lib/types"

interface SeverityBreakdownProps {
  severityData: SeverityCount
  totalCves: number
}

export function SeverityBreakdown({ severityData, totalCves }: SeverityBreakdownProps) {
  const severities = [
    {
      name: "Critical",
      count: severityData.critical,
      color: "bg-[hsl(var(--severity-critical))]",
      percentage: totalCves > 0 ? (severityData.critical / totalCves) * 100 : 0,
    },
    {
      name: "High",
      count: severityData.high,
      color: "bg-[hsl(var(--severity-high))]",
      percentage: totalCves > 0 ? (severityData.high / totalCves) * 100 : 0,
    },
    {
      name: "Medium",
      count: severityData.medium,
      color: "bg-[hsl(var(--severity-medium))]",
      percentage: totalCves > 0 ? (severityData.medium / totalCves) * 100 : 0,
    },
    {
      name: "Low",
      count: severityData.low,
      color: "bg-[hsl(var(--severity-low))]",
      percentage: totalCves > 0 ? (severityData.low / totalCves) * 100 : 0,
    },
  ]

  return (
    <Card>
      <CardHeader>
        <CardTitle>Severity Breakdown</CardTitle>
      </CardHeader>
      <CardContent className="space-y-6">
        {severities.map((severity) => (
          <div key={severity.name} className="space-y-2">
            <div className="flex items-center justify-between text-sm">
              <div className="flex items-center gap-2">
                <div className={`w-3 h-3 rounded-full ${severity.color}`} />
                <span className="font-medium">{severity.name}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="font-bold">{severity.count}</span>
                <span className="text-muted-foreground">
                  ({severity.percentage.toFixed(0)}%)
                </span>
              </div>
            </div>
            <Progress
              value={severity.percentage}
              className="h-2"
              indicatorClassName={severity.color}
            />
          </div>
        ))}
      </CardContent>
    </Card>
  )
}
