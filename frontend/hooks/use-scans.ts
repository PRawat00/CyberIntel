/**
 * React Query hooks for scan-related operations.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuth } from "@/hooks/use-auth"
import { api } from "@/lib/api"
import type { SeverityLevel } from "@/lib/types"

export function useScans(params?: {
  page?: number
  per_page?: number
  file_type?: string
}) {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["scans", user?.id, params],
    queryFn: () => api.listScans(params),
    enabled: !!user,
  })
}

export function useScan(scanId: number) {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["scan", user?.id, scanId],
    queryFn: () => api.getScan(scanId),
    enabled: !!user && !!scanId,
  })
}

export function useScanDependencies(
  scanId: number,
  params?: {
    vulnerable_only?: boolean
    severity_min?: SeverityLevel
  }
) {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["scan-dependencies", user?.id, scanId, params],
    queryFn: () => api.getScanDependencies(scanId, params),
    enabled: !!user && !!scanId,
  })
}

export function useStats() {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["stats", user?.id],
    queryFn: () => api.getStats(),
    enabled: !!user,
  })
}

export function useUploadScan() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: (file: File) => api.uploadScan(file),
    onSuccess: () => {
      // Invalidate all scans queries (regardless of params) and stats for current user
      queryClient.invalidateQueries({ queryKey: ["scans"] })
      queryClient.invalidateQueries({ queryKey: ["stats", user?.id] })
    },
  })
}

export function useDeleteScan() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: (scanId: number) => api.deleteScan(scanId),
    onSuccess: () => {
      // Invalidate all scans queries (regardless of params) and stats for current user
      queryClient.invalidateQueries({ queryKey: ["scans"] })
      queryClient.invalidateQueries({ queryKey: ["stats", user?.id] })
    },
  })
}

export function useExportScan() {
  return useMutation({
    mutationFn: ({
      scanId,
      format,
    }: {
      scanId: number
      format: "json" | "csv" | "html"
    }) => api.exportScan(scanId, format),
    onSuccess: (blob, variables) => {
      // Download the file
      const url = URL.createObjectURL(blob)
      const a = document.createElement("a")
      a.href = url
      a.download = `scan_${variables.scanId}.${variables.format}`
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
      URL.revokeObjectURL(url)
    },
  })
}
