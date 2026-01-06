'use client'

import { useState, useEffect } from 'react'
import { useSearchParams } from 'next/navigation'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Switch } from '@/components/ui/switch'
import { useToast } from '@/hooks/use-toast'
import {
  Github,
  CheckCircle,
  RefreshCw,
  AlertCircle,
  Loader2,
  MessageSquare,
  ListTodo,
  Link as LinkIcon,
  LogOut,
} from 'lucide-react'
import {
  useGitHubConnection,
  useGitHubRepos,
  useGitHubOAuthStatus,
  useConnectGitHub,
  useDisconnectGitHub,
  useSetGitHubRepo,
  useSyncGitHub,
  useToggleGitHubAutoSync,
} from '@/hooks/use-github'

export default function IntegrationsPage() {
  const searchParams = useSearchParams()
  const { toast } = useToast()
  const [selectedRepo, setSelectedRepo] = useState<string>('')

  // GitHub hooks
  const { data: connection, isLoading: connectionLoading } = useGitHubConnection()
  const { data: oauthStatus } = useGitHubOAuthStatus()
  const { data: reposData, isLoading: reposLoading } = useGitHubRepos()
  const connectGitHub = useConnectGitHub()
  const disconnectGitHub = useDisconnectGitHub()
  const setGitHubRepo = useSetGitHubRepo()
  const syncGitHub = useSyncGitHub()
  const toggleAutoSync = useToggleGitHubAutoSync()

  // Show success toast if redirected from OAuth callback
  useEffect(() => {
    if (searchParams.get('github') === 'connected') {
      toast({
        title: 'GitHub Connected',
        description: 'Your GitHub account has been connected successfully.',
      })
      // Clear the query param
      window.history.replaceState({}, '', '/dashboard/integrations')
    }
  }, [searchParams, toast])

  // Set selected repo from connection
  useEffect(() => {
    if (connection?.repo_full_name) {
      setSelectedRepo(connection.repo_full_name)
    }
  }, [connection?.repo_full_name])

  const handleConnect = () => {
    connectGitHub.mutate()
  }

  const handleDisconnect = () => {
    disconnectGitHub.mutate(undefined, {
      onSuccess: () => {
        toast({
          title: 'GitHub Disconnected',
          description: 'Your GitHub account has been disconnected.',
        })
      },
    })
  }

  const handleSetRepo = (repoFullName: string) => {
    setSelectedRepo(repoFullName)
    setGitHubRepo.mutate(repoFullName, {
      onSuccess: () => {
        toast({
          title: 'Repository Set',
          description: `Now tracking ${repoFullName}`,
        })
      },
      onError: (error) => {
        toast({
          title: 'Error',
          description: error instanceof Error ? error.message : 'Failed to set repository',
          variant: 'destructive',
        })
      },
    })
  }

  const handleSync = () => {
    syncGitHub.mutate(undefined, {
      onSuccess: (result) => {
        if (result.success) {
          toast({
            title: 'Sync Complete',
            description: `Found ${result.files_found} files, created ${result.scans_created} scans.`,
          })
        } else {
          toast({
            title: 'Sync Issue',
            description: result.error || 'Sync completed with issues',
            variant: 'destructive',
          })
        }
      },
      onError: (error) => {
        toast({
          title: 'Sync Failed',
          description: error instanceof Error ? error.message : 'Failed to sync',
          variant: 'destructive',
        })
      },
    })
  }

  const handleToggleAutoSync = () => {
    toggleAutoSync.mutate(undefined, {
      onSuccess: (result) => {
        toast({
          title: result.auto_sync_enabled ? 'Auto-sync Enabled' : 'Auto-sync Disabled',
          description: result.auto_sync_enabled
            ? 'Dependencies will sync automatically on login.'
            : 'Auto-sync has been disabled.',
        })
      },
    })
  }

  const isGitHubConnected = connection?.is_active

  return (
    <div className="container mx-auto py-8 px-4">
      {/* Header */}
      <div className="mb-6">
        <h1 className="text-3xl font-bold mb-2">Integrations</h1>
        <p className="text-muted-foreground">
          Connect external tools to automate scanning and issue tracking
        </p>
      </div>

      {/* Integrations Grid */}
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-3">
        {/* GitHub Integration Card */}
        <Card
          className={
            isGitHubConnected
              ? 'border-green-500/50 bg-green-50/5 dark:bg-green-950/10'
              : ''
          }
        >
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center mb-4">
                <Github className="h-8 w-8" />
              </div>
              {connectionLoading ? (
                <Badge className="bg-gray-400">
                  <Loader2 className="h-3 w-3 mr-1 animate-spin" />
                  Loading...
                </Badge>
              ) : (
                <Badge className={isGitHubConnected ? 'bg-green-500' : 'bg-gray-400'}>
                  {isGitHubConnected && <CheckCircle className="h-3 w-3 mr-1" />}
                  {isGitHubConnected ? 'Connected' : 'Disconnected'}
                </Badge>
              )}
            </div>
            <CardTitle>GitHub</CardTitle>
            <CardDescription>
              Sync repositories and scan dependency files automatically
            </CardDescription>
          </CardHeader>
          <CardContent>
            {connectionLoading ? (
              <div className="flex items-center justify-center py-4">
                <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
              </div>
            ) : isGitHubConnected ? (
              <div className="space-y-4">
                {/* Connected User Info */}
                <div className="flex items-center gap-3 p-3 bg-muted/50 rounded-lg">
                  {connection?.github_avatar_url && (
                    <img
                      src={connection.github_avatar_url}
                      alt={connection.github_username || ''}
                      className="w-8 h-8 rounded-full"
                    />
                  )}
                  <div>
                    <p className="font-medium text-sm">{connection?.github_username}</p>
                    {connection?.last_sync_at && (
                      <p className="text-xs text-muted-foreground">
                        Last synced: {new Date(connection.last_sync_at).toLocaleString()}
                      </p>
                    )}
                  </div>
                </div>

                {/* Sync Error */}
                {connection?.sync_error && (
                  <div className="flex items-start gap-2 p-3 bg-red-500/10 rounded-lg text-red-500">
                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <p className="text-sm">{connection.sync_error}</p>
                  </div>
                )}

                {/* Repository Selection */}
                <div className="space-y-2">
                  <Label>Repository to Track</Label>
                  <Select
                    value={selectedRepo}
                    onValueChange={handleSetRepo}
                    disabled={reposLoading || setGitHubRepo.isPending}
                  >
                    <SelectTrigger>
                      <SelectValue placeholder="Select a repository" />
                    </SelectTrigger>
                    <SelectContent>
                      {reposData?.repositories?.map((repo) => (
                        <SelectItem key={repo.full_name} value={repo.full_name}>
                          <div className="flex items-center gap-2">
                            <span>{repo.full_name}</span>
                            {repo.is_private && (
                              <Badge variant="outline" className="text-xs">Private</Badge>
                            )}
                          </div>
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>

                {/* Auto-sync Toggle */}
                <div className="flex items-center justify-between">
                  <div>
                    <Label>Auto-sync on Login</Label>
                    <p className="text-xs text-muted-foreground">
                      Automatically sync when you log in
                    </p>
                  </div>
                  <Switch
                    checked={connection?.auto_sync_enabled}
                    onCheckedChange={handleToggleAutoSync}
                    disabled={toggleAutoSync.isPending}
                  />
                </div>

                {/* Action Buttons */}
                <div className="flex gap-2">
                  <Button
                    variant="outline"
                    size="sm"
                    className="flex-1"
                    onClick={handleSync}
                    disabled={syncGitHub.isPending || !connection?.repo_full_name}
                  >
                    {syncGitHub.isPending ? (
                      <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    ) : (
                      <RefreshCw className="h-4 w-4 mr-2" />
                    )}
                    Sync Now
                  </Button>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={handleDisconnect}
                    disabled={disconnectGitHub.isPending}
                  >
                    <LogOut className="h-4 w-4 mr-2" />
                    Disconnect
                  </Button>
                </div>
              </div>
            ) : (
              <div className="space-y-3">
                {!oauthStatus?.oauth_configured && (
                  <div className="flex items-start gap-2 p-3 bg-yellow-500/10 rounded-lg text-yellow-600">
                    <AlertCircle className="h-4 w-4 mt-0.5 flex-shrink-0" />
                    <p className="text-sm">
                      GitHub integration is not configured. Contact your administrator.
                    </p>
                  </div>
                )}
                <p className="text-sm text-muted-foreground">
                  You will be able to select which repositories to grant access to.
                </p>
                <Button
                  className="w-full"
                  onClick={handleConnect}
                  disabled={connectGitHub.isPending || !oauthStatus?.oauth_configured}
                >
                  {connectGitHub.isPending ? (
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  ) : (
                    <Github className="h-4 w-4 mr-2" />
                  )}
                  Connect GitHub
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Slack Integration Card (placeholder) */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center mb-4">
                <MessageSquare className="h-8 w-8" />
              </div>
              <Badge className="bg-gray-400">Coming Soon</Badge>
            </div>
            <CardTitle>Slack</CardTitle>
            <CardDescription>
              Receive real-time alerts for vulnerabilities in Slack
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" disabled>
              Connect Slack
            </Button>
          </CardContent>
        </Card>

        {/* Jira Integration Card (placeholder) */}
        <Card>
          <CardHeader>
            <div className="flex items-start justify-between">
              <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center mb-4">
                <ListTodo className="h-8 w-8" />
              </div>
              <Badge className="bg-gray-400">Coming Soon</Badge>
            </div>
            <CardTitle>Jira</CardTitle>
            <CardDescription>
              Create and track security issues directly in Jira
            </CardDescription>
          </CardHeader>
          <CardContent>
            <Button className="w-full" disabled>
              Connect Jira
            </Button>
          </CardContent>
        </Card>
      </div>

      {/* Info Section */}
      <Card className="mt-8">
        <CardHeader>
          <CardTitle>About Integrations</CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div>
            <h4 className="font-semibold mb-2">GitHub Integration</h4>
            <p className="text-sm text-muted-foreground">
              Connect your GitHub account to automatically sync dependency files from your repositories.
              The integration will detect package.json, requirements.txt, go.mod, and other dependency
              files, then scan them for vulnerabilities. GitHub-sourced scans appear in your dashboard
              with a GitHub icon.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Slack Integration</h4>
            <p className="text-sm text-muted-foreground">
              Receive instant notifications when new vulnerabilities are discovered. Get daily
              summaries of your security posture delivered to your team channel.
            </p>
          </div>
          <div>
            <h4 className="font-semibold mb-2">Jira Integration</h4>
            <p className="text-sm text-muted-foreground">
              Create security issues automatically with detailed CVE information. Track remediation
              progress and link vulnerabilities to your development workflow.
            </p>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
