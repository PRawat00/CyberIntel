"use client"

import { UploadZone } from "@/components/scan/upload-zone"
import { SampleFiles } from "@/components/scan/sample-files"
import { AuthLoadingWrapper } from "@/components/auth/auth-loading-wrapper"

export default function UploadPage() {
  return (
    <AuthLoadingWrapper>
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
    </AuthLoadingWrapper>
  )
}
