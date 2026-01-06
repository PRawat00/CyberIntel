"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { PieChart, Pie, Cell, ResponsiveContainer, Legend, Tooltip } from "recharts"
import type { SeverityCount } from "@/lib/types"

interface SeverityChartProps {
  severityData: SeverityCount
}

const SEVERITY_COLORS = {
  critical: "hsl(0, 84%, 60%)",
  high: "hsl(24, 95%, 53%)",
  medium: "hsl(45, 93%, 47%)",
  low: "hsl(221, 83%, 53%)",
}

export function SeverityChart({ severityData }: SeverityChartProps) {
  const data = [
    { name: "Critical", value: severityData.critical, color: SEVERITY_COLORS.critical },
    { name: "High", value: severityData.high, color: SEVERITY_COLORS.high },
    { name: "Medium", value: severityData.medium, color: SEVERITY_COLORS.medium },
    { name: "Low", value: severityData.low, color: SEVERITY_COLORS.low },
  ].filter((item) => item.value > 0) // Only show non-zero values

  const total = Object.values(severityData).reduce((sum, val) => sum + val, 0)

  if (total === 0) {
    return (
      <Card>
        <CardHeader>
          <CardTitle>Severity Distribution</CardTitle>
        </CardHeader>
        <CardContent className="flex items-center justify-center h-[300px]">
          <div className="text-center">
            <p className="text-muted-foreground">No vulnerabilities found</p>
            <p className="text-sm text-muted-foreground mt-1">All scans are clean</p>
          </div>
        </CardContent>
      </Card>
    )
  }

  return (
    <Card>
      <CardHeader>
        <CardTitle>Severity Distribution</CardTitle>
      </CardHeader>
      <CardContent>
        <ResponsiveContainer width="100%" height={300}>
          <PieChart>
            <Pie
              data={data}
              cx="50%"
              cy="50%"
              labelLine={false}
              label={(props: any) => {
                const percent = props.percent as number
                const name = props.name as string
                return `${name} ${(percent * 100).toFixed(0)}%`
              }}
              outerRadius={80}
              fill="#8884d8"
              dataKey="value"
            >
              {data.map((entry, index) => (
                <Cell key={`cell-${index}`} fill={entry.color} />
              ))}
            </Pie>
            <Tooltip />
            <Legend />
          </PieChart>
        </ResponsiveContainer>

        {/* Severity breakdown */}
        <div className="grid grid-cols-2 gap-4 mt-6">
          {data.map((item) => (
            <div key={item.name} className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <div
                  className="w-3 h-3 rounded-full"
                  style={{ backgroundColor: item.color }}
                />
                <span className="text-sm font-medium">{item.name}</span>
              </div>
              <span className="text-sm font-bold">{item.value}</span>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  )
}
