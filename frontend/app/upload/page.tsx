"use client"

import { useRouter } from "next/navigation"
import { useAuth } from "@/lib/contexts/auth-context"
import { Skeleton } from "@/components/ui/skeleton"
import { UploadZone } from "@/components/scan/upload-zone"
import { SampleFiles } from "@/components/scan/sample-files"

export default function UploadPage() {
  const { user, loading } = useAuth()
  const router = useRouter()

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="container mx-auto py-12 px-4">
        <div className="max-w-7xl mx-auto">
          <div className="text-center mb-8">
            <Skeleton className="h-12 w-96 mx-auto mb-2" />
            <Skeleton className="h-6 w-64 mx-auto" />
          </div>

          <div className="flex flex-col lg:flex-row gap-6">
            <div className="flex-1 lg:w-[70%]">
              <Skeleton className="h-[400px]" />
            </div>
            <div className="lg:w-[30%]">
              <Skeleton className="h-[400px]" />
            </div>
          </div>
        </div>
      </div>
    )
  }

  // Redirect to login if not authenticated
  if (!user) {
    router.push('/auth/login')
    return null
  }

  return (
    <div className="container mx-auto py-12 px-4">
      <div className="max-w-7xl mx-auto">
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold tracking-tight mb-2">
            Scan Your Dependencies
          </h1>
          <p className="text-lg text-muted-foreground">
            Upload your dependency file to scan for vulnerabilities
          </p>
        </div>

        <div className="flex flex-col lg:flex-row gap-6">
          {/* Main upload zone - 70% width on large screens */}
          <div className="flex-1 lg:w-[70%]">
            <UploadZone />
          </div>

          {/* Sample files panel - 30% width on large screens */}
          <div className="lg:w-[30%]">
            <SampleFiles />
          </div>
        </div>
      </div>
    </div>
  )
}
