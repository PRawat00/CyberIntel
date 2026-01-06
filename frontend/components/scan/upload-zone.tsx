"use client"

import { useCallback, useState } from "react"
import { useRouter } from "next/navigation"
import { useDropzone } from "react-dropzone"
import { Upload, File as FileIcon, CheckCircle2, XCircle, Loader2, Github } from "lucide-react"
import { motion, AnimatePresence } from "framer-motion"
import { useUploadScan } from "@/hooks/use-scans"
import { useToast } from "@/hooks/use-toast"
import { useNavigationState } from "@/hooks/use-navigation-state"
import { api } from "@/lib/api"
import { Card, CardContent } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Progress } from "@/components/ui/progress"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Badge } from "@/components/ui/badge"
import { fadeIn, smooth } from "@/lib/animations"
import { GitHubRepoBrowser } from "@/components/github/repo-browser"

const ALLOWED_EXTENSIONS = [".json", ".txt", ".lock", ".in", ".toml", ".mod", ".sum"]
const MAX_FILE_SIZE = 1 * 1024 * 1024 // 1MB

interface UploadState {
  status: "idle" | "uploading" | "success" | "error"
  progress: number
  fileName?: string
  error?: string
}

export function UploadZone() {
  const router = useRouter()
  const uploadMutation = useUploadScan()
  const { toast } = useToast()
  const { setSelectedScanId } = useNavigationState()
  const [uploadState, setUploadState] = useState<UploadState>({
    status: "idle",
    progress: 0,
  })

  const processFile = useCallback(
    async (file: File) => {
      // Validate file extension
      const ext = file.name.substring(file.name.lastIndexOf(".")).toLowerCase()
      if (!ALLOWED_EXTENSIONS.includes(ext)) {
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: `Invalid file type. Allowed: ${ALLOWED_EXTENSIONS.join(", ")}`,
        })
        return
      }

      // Validate file size
      if (file.size > MAX_FILE_SIZE) {
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: `File too large. Max size: ${MAX_FILE_SIZE / 1024 / 1024}MB`,
        })
        return
      }

      // Start upload
      setUploadState({
        status: "uploading",
        progress: 0,
        fileName: file.name,
      })

      // Simulate progress (since we don't have real progress from fetch)
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
          description: `Found ${scan.total_cves} vulnerabilities in ${scan.total_dependencies} dependencies`,
          variant: "success",
        })

        // Set the selected scan ID in navigation state so it's selected in the sidebar
        setSelectedScanId(scan.id)

        // Redirect to dependencies page where the file list sidebar is shown
        setTimeout(() => {
          router.push(`/dashboard/dependencies`)
        }, 1000)
      } catch (error) {
        clearInterval(progressInterval)
        const errorMessage = error instanceof Error ? error.message : "Upload failed"
        setUploadState({
          status: "error",
          progress: 0,
          fileName: file.name,
          error: errorMessage,
        })

        toast({
          title: "Upload failed",
          description: errorMessage,
          variant: "destructive",
        })
      }
    },
    [uploadMutation, router, toast, setSelectedScanId]
  )

  const onDrop = useCallback(
    async (acceptedFiles: File[]) => {
      // Handle regular file drop
      if (acceptedFiles.length === 0) return
      const file = acceptedFiles[0]
      await processFile(file)
    },
    [processFile]
  )

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      "application/json": [".json", ".lock"],
      "text/plain": [".txt", ".in"],
      "application/toml": [".toml"],
      "text/x-go": [".mod", ".sum"],
    },
    maxFiles: 1,
    maxSize: MAX_FILE_SIZE,
  })

  const handleSampleFileDrop = useCallback(
    async (sampleFileName: string) => {
      // Fetch sample file from API
      try {
        const blob = await api.getSampleFile(sampleFileName)
        const file = new File([blob], sampleFileName, { type: blob.type })
        await processFile(file)
      } catch (error) {
        setUploadState({
          status: "error",
          progress: 0,
          fileName: sampleFileName,
          error: error instanceof Error ? error.message : "Failed to load sample file",
        })

        toast({
          title: "Error",
          description: "Failed to load sample file",
          variant: "destructive",
        })
      }
    },
    [processFile, toast]
  )

  const handleGitHubImport = useCallback(
    async (repo: any, file: any) => {
      // Start the import process
      setUploadState({
        status: "uploading",
        progress: 0,
        fileName: `${repo.name}/${file.name}`,
      })

      // Simulate progress
      const progressInterval = setInterval(() => {
        setUploadState((prev) => ({
          ...prev,
          progress: Math.min(prev.progress + 10, 90),
        }))
      }, 200)

      try {
        // Import and scan the file from GitHub
        const response = await api.post("/github/scan", {
          owner: repo.owner,
          repo: repo.name,
          file_path: file.path,
          branch: repo.default_branch,
        })

        clearInterval(progressInterval)

        if (response.success) {
          setUploadState({
            status: "success",
            progress: 100,
            fileName: `${repo.name}/${file.name}`,
          })

          toast({
            title: "GitHub import successful!",
            description: `Found ${response.total_cves || 0} vulnerabilities in ${response.total_dependencies} dependencies`,
            variant: "success",
          })

          // Set the selected scan ID
          if (response.scan_id) {
            setSelectedScanId(response.scan_id)
          }

          // Redirect to dependencies page
          setTimeout(() => {
            router.push(`/dashboard/dependencies`)
          }, 1000)
        } else {
          throw new Error(response.message || "Import failed")
        }
      } catch (error) {
        clearInterval(progressInterval)
        const errorMessage = error instanceof Error ? error.message : "GitHub import failed"

        setUploadState({
          status: "error",
          progress: 0,
          fileName: `${repo.name}/${file.name}`,
          error: errorMessage,
        })

        toast({
          title: "Import failed",
          description: errorMessage,
          variant: "destructive",
        })
      }
    },
    [router, toast, setSelectedScanId]
  )

  const resetUpload = () => {
    setUploadState({
      status: "idle",
      progress: 0,
    })
  }

  // Get base dropzone props and override with custom drag handlers
  const dropzoneProps = getRootProps()

  const customDropzoneProps = {
    ...dropzoneProps,
    onDragOver: (e: React.DragEvent) => {
      // Check if it's a sample file
      if (e.dataTransfer.types.includes("application/x-sample-file")) {
        e.preventDefault()
        e.stopPropagation()
        e.dataTransfer.dropEffect = "copy"
      } else {
        // Let react-dropzone handle regular files
        dropzoneProps.onDragOver?.(e as React.DragEvent<HTMLElement>)
      }
    },
    onDrop: async (e: React.DragEvent) => {
      // Check for sample file data
      const sampleFileName = e.dataTransfer.getData("application/x-sample-file")

      if (sampleFileName) {
        e.preventDefault()
        e.stopPropagation()
        await handleSampleFileDrop(sampleFileName)
      } else {
        // Let react-dropzone handle regular files
        dropzoneProps.onDrop?.(e as React.DragEvent<HTMLElement>)
      }
    },
  }

  return (
    <div className="w-full space-y-4">
      <motion.div
        initial="initial"
        animate="animate"
        variants={fadeIn}
        transition={smooth}
      >
        <Card
          {...customDropzoneProps}
          className={`
            border-2 border-dashed transition-all duration-200 cursor-pointer
            ${isDragActive ? "border-primary bg-primary/5 scale-105" : "border-border hover:border-primary/50"}
            ${uploadState.status === "uploading" ? "pointer-events-none" : ""}
          `}
        >
          <CardContent className="flex flex-col items-center justify-center p-12 text-center">
            <input {...getInputProps()} />

          <AnimatePresence mode="wait">
            {uploadState.status === "idle" && (
              <motion.div
                key="idle"
                variants={fadeIn}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={smooth}
                className="flex flex-col items-center"
              >
                <Upload className="w-16 h-16 mb-4 text-muted-foreground" />
                <h3 className="text-xl font-semibold mb-2">
                  {isDragActive ? "Drop your file here" : "Upload dependency file"}
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  Drag and drop or click to browse
                </p>
                <div className="flex flex-wrap gap-2 justify-center">
                  {ALLOWED_EXTENSIONS.map((ext) => (
                    <Badge key={ext} variant="secondary" className="text-xs">
                      {ext}
                    </Badge>
                  ))}
                </div>
                <p className="text-xs text-muted-foreground mt-4">
                  Max file size: {MAX_FILE_SIZE / 1024 / 1024}MB
                </p>
              </motion.div>
            )}

            {uploadState.status === "uploading" && (
              <motion.div
                key="uploading"
                variants={fadeIn}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={smooth}
                className="flex flex-col items-center"
              >
                <Loader2 className="w-16 h-16 mb-4 text-primary animate-spin" />
                <h3 className="text-xl font-semibold mb-2">Scanning...</h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {uploadState.fileName}
                </p>
                <Progress value={uploadState.progress} className="w-full max-w-xs" />
                <p className="text-xs text-muted-foreground mt-2">
                  {uploadState.progress}% complete
                </p>
              </motion.div>
            )}

            {uploadState.status === "success" && (
              <motion.div
                key="success"
                variants={fadeIn}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={smooth}
                className="flex flex-col items-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                >
                  <CheckCircle2 className="w-16 h-16 mb-4 text-green-500" />
                </motion.div>
                <h3 className="text-xl font-semibold mb-2 text-green-600 dark:text-green-400">
                  Scan complete!
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {uploadState.fileName}
                </p>
                <p className="text-xs text-muted-foreground">
                  Redirecting to results...
                </p>
              </motion.div>
            )}

            {uploadState.status === "error" && (
              <motion.div
                key="error"
                variants={fadeIn}
                initial="initial"
                animate="animate"
                exit="exit"
                transition={smooth}
                className="flex flex-col items-center"
              >
                <motion.div
                  initial={{ scale: 0 }}
                  animate={{ scale: 1 }}
                  transition={{ type: "spring", stiffness: 200, damping: 15 }}
                >
                  <XCircle className="w-16 h-16 mb-4 text-red-500" />
                </motion.div>
                <h3 className="text-xl font-semibold mb-2 text-red-600 dark:text-red-400">
                  Upload failed
                </h3>
                <p className="text-sm text-muted-foreground mb-4">
                  {uploadState.fileName}
                </p>
                <Alert variant="destructive" className="max-w-md">
                  <AlertDescription>{uploadState.error}</AlertDescription>
                </Alert>
                <Button onClick={resetUpload} className="mt-4" variant="outline">
                  Try again
                </Button>
              </motion.div>
            )}
          </AnimatePresence>
        </CardContent>
      </Card>
      </motion.div>

      {uploadState.status === "idle" && (
        <>
          {/* GitHub Import Button */}
          <div className="flex justify-center">
            <div className="flex items-center gap-4">
              <span className="text-sm text-muted-foreground">or</span>
              <GitHubRepoBrowser
                onImport={handleGitHubImport}
                trigger={
                  <Button variant="outline" className="gap-2">
                    <Github className="h-4 w-4" />
                    Import from GitHub
                  </Button>
                }
              />
            </div>
          </div>

          <div className="text-center text-sm text-muted-foreground">
            <p className="font-medium mb-2">Supported file types:</p>
            <div className="space-y-1">
              <p>
                <strong>npm:</strong> package.json, package-lock.json
              </p>
              <p>
                <strong>Python:</strong> requirements.txt, Pipfile
              </p>
              <p>
                <strong>Go:</strong> go.mod, go.sum (coming soon)
              </p>
            </div>
          </div>
        </>
      )}
    </div>
  )
}
