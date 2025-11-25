"use client"

import { Suspense, useEffect, useState } from "react"
import { useSearchParams, useRouter } from "next/navigation"
import { api } from "@/lib/api"
import { Loader2, CheckCircle2, XCircle } from "lucide-react"

type CallbackStatus = "processing" | "success" | "error"

function GitHubCallbackContent() {
  const searchParams = useSearchParams()
  const router = useRouter()
  const [status, setStatus] = useState<CallbackStatus>("processing")
  const [message, setMessage] = useState("")

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get("code")
      const state = searchParams.get("state")
      const error = searchParams.get("error")

      // Check for OAuth errors from GitHub
      if (error) {
        const errorDescription = searchParams.get("error_description") || error
        setStatus("error")
        setMessage(`GitHub authorization failed: ${errorDescription}`)
        return
      }

      if (!code || !state) {
        setStatus("error")
        setMessage("Missing authorization code or state parameter.")
        return
      }

      // Verify state matches what we stored
      const storedState = sessionStorage.getItem("github-oauth-state")
      if (storedState && storedState !== state) {
        setStatus("error")
        setMessage("State mismatch. This could be a CSRF attack. Please try again.")
        return
      }

      // Clear stored state
      sessionStorage.removeItem("github-oauth-state")

      try {
        const result = await api.handleGitHubCallback(code, state)

        if (result.success) {
          setStatus("success")
          setMessage(`Connected as ${result.github_username}`)
          // Redirect to integrations page after a short delay
          setTimeout(() => {
            router.push("/dashboard/integrations?github=connected")
          }, 1500)
        } else {
          setStatus("error")
          setMessage(result.message || "Failed to connect GitHub.")
        }
      } catch (error) {
        setStatus("error")
        setMessage(error instanceof Error ? error.message : "An unexpected error occurred.")
      }
    }

    handleCallback()
  }, [searchParams, router])

  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg">
      <div className="text-center p-8 rounded-lg bg-dark-surface border border-dark-border max-w-md w-full mx-4">
        {status === "processing" && (
          <>
            <Loader2 className="h-12 w-12 animate-spin text-brand-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-100 mb-2">
              Connecting GitHub...
            </h2>
            <p className="text-slate-400">
              Please wait while we complete the connection.
            </p>
          </>
        )}

        {status === "success" && (
          <>
            <CheckCircle2 className="h-12 w-12 text-green-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-100 mb-2">
              GitHub Connected!
            </h2>
            <p className="text-slate-400 mb-4">{message}</p>
            <p className="text-sm text-slate-500">Redirecting to integrations...</p>
          </>
        )}

        {status === "error" && (
          <>
            <XCircle className="h-12 w-12 text-red-500 mx-auto mb-4" />
            <h2 className="text-xl font-semibold text-slate-100 mb-2">
              Connection Failed
            </h2>
            <p className="text-slate-400 mb-4">{message}</p>
            <button
              onClick={() => router.push("/dashboard/integrations")}
              className="px-4 py-2 bg-brand-500 text-white rounded-md hover:bg-brand-600 transition-colors"
            >
              Return to Integrations
            </button>
          </>
        )}
      </div>
    </div>
  )
}

function LoadingFallback() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-dark-bg">
      <div className="text-center p-8 rounded-lg bg-dark-surface border border-dark-border max-w-md w-full mx-4">
        <Loader2 className="h-12 w-12 animate-spin text-brand-500 mx-auto mb-4" />
        <h2 className="text-xl font-semibold text-slate-100 mb-2">
          Loading...
        </h2>
      </div>
    </div>
  )
}

export default function GitHubCallbackPage() {
  return (
    <Suspense fallback={<LoadingFallback />}>
      <GitHubCallbackContent />
    </Suspense>
  )
}
