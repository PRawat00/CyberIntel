"use client"

import { useCallback, useState, useEffect, useRef } from "react"
import { useDropzone } from "react-dropzone"
import { Upload, FileText, AlertTriangle, CheckCircle2, Loader2, XCircle } from "lucide-react"
import { formatDistanceToNow } from "date-fns"
import { useUploadScan, useScans } from "@/hooks/use-scans"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { useToast } from "@/hooks/use-toast"
import { logger } from "@/lib/logger"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Progress } from "@/components/ui/progress"
import { Skeleton } from "@/components/ui/skeleton"
import type { ScanSummary } from "@/lib/types"

const ALLOWED_EXTENSIONS = [".json", ".txt", ".lock", ".in", ".toml", ".mod", ".sum"]
const MAX_FILE_SIZE = 1 * 1024 * 1024 // 1MB

interface UploadState {
  status: "idle" | "uploading" | "success" | "error"
  progress: number
  fileName?: string
  error?: string
}

export function SidebarL2Dependencies() {
  const { data: scansResponse, isLoading, error } = useScans()
  const uploadMutation = useUploadScan()
  const { toast } = useToast()
  const { selectedScanId, setSelectedScanId } = useNavigationState()
  const [uploadState, setUploadState] = useState<UploadState>({
    status: "idle",
    progress: 0,
  })
  const hasAutoSelected = useRef(false)

  // Debug logging
  useEffect(() => {
    logger.log('[SIDEBAR] Scans query state:', {
      isLoading,
      hasError: !!error,
      error: error,
      hasData: !!scansResponse,
      scansCount: scansResponse?.scans?.length || 0
    })
  }, [isLoading, error, scansResponse])

  // Auto-select first scan when list loads and nothing is selected (only once)
  useEffect(() => {
    if (
      !hasAutoSelected.current &&
      scansResponse?.scans &&
      scansResponse.scans.length > 0 &&
      !selectedScanId
    ) {
      setSelectedScanId(scansResponse.scans[0].id)
      hasAutoSelected.current = true
    }
  }, [scansResponse?.scans?.length, selectedScanId, setSelectedScanId])

  const processFile = useCallback(
    async (file: File) => {
      // Validate file extension
      const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: `Invalid file type`,
        })
        return
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: `File too large (max 1MB)`,
        })
        return
      }

      // Start upload
      setUploadState({
        status: "uploading",
        progress: 0,
        fileName: file.name,
      })

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadState((prev) => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }))
      }, 200)

      try {
        const scan = await uploadMutation.mutateAsync(file)

        clearInterval(progressInterval)
        setUploadState({
          status: "success",
          progress: 100,
          fileName: file.name,
        })

        toast({
          title: "Scan complete!",
          description: `Found ${scan.total_cves} vulnerabilities`,
        })

        // Auto-select the new scan
        setSelectedScanId(scan.id)

        // Reset upload state after 2 seconds
        setTimeout(() => {
          setUploadState({ status: "idle", progress: 0 })
        }, 2000)
      } catch (error) {
        clearInterval(progressInterval)
        const errorMessage = error instanceof Error ? error.message : "Upload failed"
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: errorMessage,
        })
      }
    },
    [uploadMutation, setSelectedScanId, toast]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop: (acceptedFiles) => {
      if (acceptedFiles.length > 0) {
        processFile(acceptedFiles[0])
      }
    },
    accept: {
      "application/json": [".json"],
      "text/plain": [".txt", ".lock", ".in", ".toml", ".mod", ".sum"],
    },
    maxFiles: 1,
    disabled: uploadState.status === "uploading",
  })

  const scans = scansResponse?.scans || []

  return (
    <div className="flex flex-col h-full">
      {/* Compact Upload Zone */}
      <div className="p-4 border-b border-dark-border">
        <div
          {...getRootProps()}
          className={cn(
            "border-2 border-dashed rounded-lg p-4 cursor-pointer transition-colors",
            isDragActive && "border-brand-500 bg-brand-500/5",
            uploadState.status === "uploading" && "cursor-not-allowed opacity-60",
            uploadState.status === "idle" && "border-dark-border hover:border-brand-500/50 hover:bg-dark-hover"
          )}
        >
          <input {...getInputProps()} />

          {uploadState.status === "idle" && (
            <div className="flex flex-col items-center text-center gap-2">
              <Upload className="h-8 w-8 text-slate-400" />
              <div>
                <p className="text-sm font-medium text-slate-300">Drop file here</p>
                <p className="text-xs text-slate-500 mt-1">or click to browse</p>
              </div>
            </div>
          )}

          {uploadState.status === "uploading" && (
            <div className="flex flex-col items-center gap-2">
              <Loader2 className="h-8 w-8 text-brand-500 animate-spin" />
              <p className="text-sm font-medium text-slate-300">{uploadState.fileName}</p>
              <Progress value={uploadState.progress} className="w-full" />
            </div>
          )}

          {uploadState.status === "success" && (
            <div className="flex flex-col items-center gap-2">
              <CheckCircle2 className="h-8 w-8 text-green-500" />
              <p className="text-sm font-medium text-green-400">Upload complete!</p>
            </div>
          )}

          {uploadState.status === "error" && (
            <div className="flex flex-col items-center gap-2">
              <XCircle className="h-8 w-8 text-red-500" />
              <p className="text-sm font-medium text-red-400">{uploadState.error}</p>
              <Button
                size="sm"
                variant="ghost"
                onClick={() => setUploadState({ status: "idle", progress: 0 })}
                className="text-xs"
              >
                Try again
              </Button>
            </div>
          )}
        </div>
      </div>

      {/* Scans List */}
      <div className="flex-1 overflow-y-auto">
        <div className="p-4">
          <h3 className="text-sm font-semibold text-slate-400 mb-3">My Scans</h3>

          {isLoading && (
            <div className="space-y-3">
              {[1, 2, 3].map((i) => (
                <Skeleton key={i} className="h-16 w-full" />
              ))}
            </div>
          )}

          {!isLoading && error && (
            <div className="text-center py-8">
              <AlertTriangle className="h-12 w-12 text-red-500 mx-auto mb-2" />
              <p className="text-sm text-red-400">Failed to load scans</p>
              <p className="text-xs text-slate-600 mt-1">
                {error instanceof Error ? error.message : 'Unknown error'}
              </p>
              <p className="text-xs text-slate-700 mt-2">Check browser console for details</p>
            </div>
          )}

          {!isLoading && !error && scans.length === 0 && (
            <div className="text-center py-8">
              <FileText className="h-12 w-12 text-slate-600 mx-auto mb-2" />
              <p className="text-sm text-slate-500">No scans yet</p>
              <p className="text-xs text-slate-600 mt-1">Upload a file to get started</p>
            </div>
          )}

          {!isLoading && scans.length > 0 && (
            <div className="space-y-2">
              {scans.map((scan) => (
                <ScanItem
                  key={scan.id}
                  scan={scan}
                  isSelected={selectedScanId === scan.id}
                  onSelect={() => {
                    logger.log('[SIDEBAR] Scan clicked:', scan.id, scan.file_name)
                    setSelectedScanId(scan.id)
                  }}
                />
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  )
}

interface ScanItemProps {
  scan: ScanSummary
  isSelected: boolean
  onSelect: () => void
}

function ScanItem({ scan, isSelected, onSelect }: ScanItemProps) {
  const hasVulnerabilities = scan.vulnerable_dependencies > 0

  return (
    <button
      onClick={onSelect}
      className={cn(
        "w-full text-left p-3 rounded-lg border transition-all",
        isSelected
          ? "border-brand-500 bg-brand-500/10"
          : "border-dark-border hover:border-slate-600 hover:bg-dark-hover"
      )}
    >
      <div className="flex items-start gap-2">
        <div className="mt-0.5">
          {hasVulnerabilities ? (
            <AlertTriangle className="h-4 w-4 text-orange-500" />
          ) : (
            <CheckCircle2 className="h-4 w-4 text-green-500" />
          )}
        </div>

        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <p className="text-sm font-medium text-slate-200 truncate">{scan.file_name}</p>
            {isSelected && (
              <Badge variant="default" className="text-xs bg-brand-600">
                Active
              </Badge>
            )}
          </div>

          <div className="flex items-center gap-2 text-xs text-slate-500">
            <span>{scan.total_dependencies} deps</span>
            {hasVulnerabilities && (
              <span className="text-orange-400 font-medium">
                {scan.vulnerable_dependencies} vuln
              </span>
            )}
          </div>

          <div className="flex items-center gap-1 mt-1.5">
            {scan.severity_counts.critical > 0 && (
              <Badge className="text-xs bg-[hsl(var(--severity-critical))] text-white px-1.5 py-0">
                {scan.severity_counts.critical}
              </Badge>
            )}
            {scan.severity_counts.high > 0 && (
              <Badge className="text-xs bg-[hsl(var(--severity-high))] text-white px-1.5 py-0">
                {scan.severity_counts.high}
              </Badge>
            )}
            {scan.severity_counts.medium > 0 && (
              <Badge className="text-xs bg-[hsl(var(--severity-medium))] text-white px-1.5 py-0">
                {scan.severity_counts.medium}
              </Badge>
            )}
          </div>

          <p className="text-xs text-slate-600 mt-1">
            {formatDistanceToNow(new Date(scan.scan_date), { addSuffix: true })}
          </p>
        </div>
      </div>
    </button>
  )
}
