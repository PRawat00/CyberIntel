"use client"

import { useState } from "react"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { Button } from "@/components/ui/button"
import { Separator } from "@/components/ui/separator"
import { Badge } from "@/components/ui/badge"
import { User, Bell, Key, Shield, Github, Check, X, Loader2, ExternalLink } from "lucide-react"
import { useToast } from "@/hooks/use-toast"
import { api } from "@/lib/api"

// Placeholder Switch component
function Switch({ defaultChecked }: { defaultChecked?: boolean }) {
  return (
    <button
      className="relative inline-flex h-6 w-11 items-center rounded-full bg-slate-700 transition-colors hover:bg-slate-600"
      aria-label="Toggle"
    >
      <span className={`${defaultChecked ? 'translate-x-6' : 'translate-x-1'} inline-block h-4 w-4 transform rounded-full bg-white transition-transform`} />
    </button>
  )
}

export default function SettingsPage() {
  const [githubToken, setGithubToken] = useState("")
  const [isTestingConnection, setIsTestingConnection] = useState(false)
  const [isSavingToken, setIsSavingToken] = useState(false)
  const [connectionStatus, setConnectionStatus] = useState<{
    success?: boolean
    message?: string
    username?: string
  } | null>(null)
  const { toast } = useToast()

  const handleSaveGitHubToken = async () => {
    if (!githubToken.trim()) {
      toast({
        title: "Error",
        description: "Please enter a GitHub Personal Access Token",
        variant: "destructive"
      })
      return
    }

    setIsSavingToken(true)
    setConnectionStatus(null)

    try {
      const response = await api.post("/github/save-token", { token: githubToken })

      if (response.success) {
        setConnectionStatus({
          success: true,
          message: "GitHub token saved successfully",
          username: response.username
        })
        toast({
          title: "Success",
          description: `GitHub token saved for @${response.username}`,
        })
      } else {
        throw new Error(response.message || "Failed to save token")
      }
    } catch (error: any) {
      const message = error.message || "Failed to save GitHub token"
      setConnectionStatus({
        success: false,
        message
      })
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      })
    } finally {
      setIsSavingToken(false)
    }
  }

  const handleTestConnection = async () => {
    setIsTestingConnection(true)
    setConnectionStatus(null)

    try {
      const response = await api.get("/github/test-connection")

      if (response.success) {
        setConnectionStatus({
          success: true,
          message: "Connection successful",
          username: response.username
        })
        toast({
          title: "Success",
          description: `Connected to GitHub as @${response.username}`,
        })
      } else {
        throw new Error(response.message || "Connection failed")
      }
    } catch (error: any) {
      const message = error.message || "Failed to test connection"
      setConnectionStatus({
        success: false,
        message
      })
      toast({
        title: "Error",
        description: message,
        variant: "destructive"
      })
    } finally {
      setIsTestingConnection(false)
    }
  }

  return (
    <div className="container mx-auto py-6 px-4 max-w-4xl">
      <div className="space-y-6">
        {/* Page Header */}
        <div>
          <h1 className="text-3xl font-bold text-slate-100">Settings</h1>
          <p className="text-slate-400 mt-1">Manage your account and application preferences</p>
        </div>

        {/* Profile Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <User className="h-5 w-5" />
              Profile
            </CardTitle>
            <CardDescription>Manage your personal information</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div className="space-y-2">
                <Label htmlFor="firstName">First Name</Label>
                <Input id="firstName" placeholder="John" />
              </div>
              <div className="space-y-2">
                <Label htmlFor="lastName">Last Name</Label>
                <Input id="lastName" placeholder="Doe" />
              </div>
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" placeholder="john@example.com" />
            </div>
            <Button>Save Changes</Button>
          </CardContent>
        </Card>

        {/* GitHub Integration */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Github className="h-5 w-5" />
              GitHub Integration
            </CardTitle>
            <CardDescription>
              Connect your GitHub account to import dependency files directly from repositories
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="githubToken">Personal Access Token</Label>
              <div className="flex gap-2">
                <Input
                  id="githubToken"
                  type="password"
                  placeholder="ghp_xxxxxxxxxxxxxxxxxxxx"
                  value={githubToken}
                  onChange={(e) => setGithubToken(e.target.value)}
                  className="flex-1"
                />
                <Button
                  onClick={handleSaveGitHubToken}
                  disabled={isSavingToken || !githubToken}
                >
                  {isSavingToken ? (
                    <>
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                      Saving...
                    </>
                  ) : (
                    "Save Token"
                  )}
                </Button>
              </div>
              <p className="text-sm text-muted-foreground">
                Create a token at{" "}
                <a
                  href="https://github.com/settings/tokens/new"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline inline-flex items-center gap-1"
                >
                  GitHub Settings
                  <ExternalLink className="h-3 w-3" />
                </a>
                {" "}with <code className="text-xs bg-slate-800 px-1 py-0.5 rounded">repo</code> scope
              </p>
            </div>

            {/* Connection Status */}
            {connectionStatus && (
              <div
                className={`p-3 rounded-lg flex items-center gap-2 ${
                  connectionStatus.success
                    ? "bg-green-500/10 border border-green-500/20 text-green-400"
                    : "bg-red-500/10 border border-red-500/20 text-red-400"
                }`}
              >
                {connectionStatus.success ? (
                  <Check className="h-4 w-4" />
                ) : (
                  <X className="h-4 w-4" />
                )}
                <div className="flex-1">
                  <p className="text-sm font-medium">{connectionStatus.message}</p>
                  {connectionStatus.username && (
                    <p className="text-xs opacity-80">Connected as @{connectionStatus.username}</p>
                  )}
                </div>
              </div>
            )}

            <div className="flex gap-2">
              <Button
                variant="outline"
                onClick={handleTestConnection}
                disabled={isTestingConnection}
              >
                {isTestingConnection ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Testing...
                  </>
                ) : (
                  "Test Connection"
                )}
              </Button>
              <Button
                variant="outline"
                onClick={() => window.location.href = "/dashboard/dependencies"}
              >
                Import from GitHub
              </Button>
            </div>
          </CardContent>
        </Card>

        {/* Notification Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Bell className="h-5 w-5" />
              Notifications
            </CardTitle>
            <CardDescription>Configure how you receive alerts</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Email Notifications</Label>
                <p className="text-sm text-muted-foreground">
                  Receive email alerts for new vulnerabilities
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Critical Alerts Only</Label>
                <p className="text-sm text-muted-foreground">
                  Only notify for critical severity issues
                </p>
              </div>
              <Switch />
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Weekly Summary</Label>
                <p className="text-sm text-muted-foreground">
                  Receive a weekly digest of scan results
                </p>
              </div>
              <Switch defaultChecked />
            </div>
          </CardContent>
        </Card>

        {/* API Keys */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Key className="h-5 w-5" />
              API Keys
            </CardTitle>
            <CardDescription>Manage API access tokens</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="space-y-2">
              <div className="flex items-center justify-between p-3 border border-dark-border rounded-lg">
                <div>
                  <p className="font-medium">Production API Key</p>
                  <p className="text-sm text-muted-foreground">Created 30 days ago</p>
                </div>
                <Badge variant="outline" className="text-green-400 border-green-400">
                  Active
                </Badge>
              </div>
              <div className="flex items-center justify-between p-3 border border-dark-border rounded-lg">
                <div>
                  <p className="font-medium">Development API Key</p>
                  <p className="text-sm text-muted-foreground">Created 15 days ago</p>
                </div>
                <Badge variant="outline" className="text-green-400 border-green-400">
                  Active
                </Badge>
              </div>
            </div>
            <Button variant="outline">Generate New Key</Button>
          </CardContent>
        </Card>

        {/* Security Settings */}
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security
            </CardTitle>
            <CardDescription>Manage authentication and security preferences</CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Two-Factor Authentication</Label>
                <p className="text-sm text-muted-foreground">
                  Add an extra layer of security to your account
                </p>
              </div>
              <Button variant="outline" size="sm">
                Enable
              </Button>
            </div>
            <Separator />
            <div className="flex items-center justify-between">
              <div className="space-y-0.5">
                <Label>Password</Label>
                <p className="text-sm text-muted-foreground">Last changed 60 days ago</p>
              </div>
              <Button variant="outline" size="sm">
                Change
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
