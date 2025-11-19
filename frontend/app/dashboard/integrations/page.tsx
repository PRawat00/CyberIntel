'use client'

import { useState } from 'react'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
import { Github, CheckCircle, Settings, Link as LinkIcon, MessageSquare, ListTodo } from 'lucide-react'
import type { Integration } from '@/lib/types'

// Mock integrations data
const INITIAL_INTEGRATIONS: Integration[] = [
  {
    id: 'github',
    name: 'GitHub',
    type: 'github',
    status: 'connected',
    config: {
      repositories: 5,
      auto_scan: true,
    },
    last_sync: new Date().toISOString(),
  },
  {
    id: 'slack',
    name: 'Slack',
    type: 'slack',
    status: 'disconnected',
  },
  {
    id: 'jira',
    name: 'Jira',
    type: 'jira',
    status: 'disconnected',
  },
]

export default function IntegrationsPage() {
  const [integrations, setIntegrations] = useState<Integration[]>(INITIAL_INTEGRATIONS)
  const [selectedIntegration, setSelectedIntegration] = useState<Integration | null>(null)

  const getIntegrationIcon = (type: string) => {
    switch (type) {
      case 'github':
        return <Github className="h-8 w-8" />
      case 'slack':
        return <MessageSquare className="h-8 w-8" />
      case 'jira':
        return <ListTodo className="h-8 w-8" />
      default:
        return <LinkIcon className="h-8 w-8" />
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'connected':
        return 'bg-green-500'
      case 'error':
        return 'bg-red-500'
      default:
        return 'bg-gray-400'
    }
  }

  const handleConnect = (integration: Integration) => {
    setIntegrations((prev) =>
      prev.map((int) =>
        int.id === integration.id
          ? { ...int, status: 'connected', last_sync: new Date().toISOString() }
          : int
      )
    )
  }

  const handleDisconnect = (integration: Integration) => {
    setIntegrations((prev) =>
      prev.map((int) =>
        int.id === integration.id ? { ...int, status: 'disconnected', last_sync: undefined } : int
      )
    )
  }

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
        {integrations.map((integration) => (
          <Card
            key={integration.id}
            className={
              integration.status === 'connected'
                ? 'border-green-500/50 bg-green-50/5 dark:bg-green-950/10'
                : ''
            }
          >
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="w-12 h-12 rounded-lg bg-muted flex items-center justify-center mb-4">
                  {getIntegrationIcon(integration.type)}
                </div>
                <Badge className={getStatusColor(integration.status)}>
                  {integration.status === 'connected' && <CheckCircle className="h-3 w-3 mr-1" />}
                  {integration.status === 'connected' ? 'Connected' : 'Disconnected'}
                </Badge>
              </div>
              <CardTitle>{integration.name}</CardTitle>
              <CardDescription>
                {integration.type === 'github' &&
                  'Sync repositories and scan pull requests automatically'}
                {integration.type === 'slack' &&
                  'Receive real-time alerts for vulnerabilities in Slack'}
                {integration.type === 'jira' &&
                  'Create and track security issues directly in Jira'}
              </CardDescription>
            </CardHeader>
            <CardContent>
              {integration.status === 'connected' ? (
                <div className="space-y-3">
                  {integration.last_sync && (
                    <p className="text-xs text-muted-foreground">
                      Last synced: {new Date(integration.last_sync).toLocaleString()}
                    </p>
                  )}
                  {integration.config && integration.type === 'github' && (
                    <p className="text-sm">
                      Monitoring {(integration.config as any).repositories} repositories
                    </p>
                  )}
                  <div className="flex gap-2">
                    <Dialog>
                      <DialogTrigger asChild>
                        <Button
                          variant="outline"
                          size="sm"
                          className="flex-1"
                          onClick={() => setSelectedIntegration(integration)}
                        >
                          <Settings className="h-4 w-4 mr-2" />
                          Configure
                        </Button>
                      </DialogTrigger>
                      <DialogContent>
                        <DialogHeader>
                          <DialogTitle>Configure {integration.name}</DialogTitle>
                          <DialogDescription>
                            Manage settings for this integration
                          </DialogDescription>
                        </DialogHeader>
                        <div className="space-y-4 py-4">
                          {integration.type === 'github' && (
                            <>
                              <div className="space-y-2">
                                <Label>Repository URL</Label>
                                <Input placeholder="https://github.com/user/repo" />
                              </div>
                              <div className="space-y-2">
                                <Label>Access Token</Label>
                                <Input type="password" placeholder="ghp_..." />
                              </div>
                              <div className="flex items-center space-x-2">
                                <input
                                  type="checkbox"
                                  id="auto-scan"
                                  className="rounded border-gray-300"
                                  defaultChecked
                                />
                                <Label htmlFor="auto-scan">Automatically scan pull requests</Label>
                              </div>
                            </>
                          )}
                          {integration.type === 'slack' && (
                            <>
                              <div className="space-y-2">
                                <Label>Webhook URL</Label>
                                <Input placeholder="https://hooks.slack.com/services/..." />
                              </div>
                              <div className="space-y-2">
                                <Label>Channel</Label>
                                <Input placeholder="#security-alerts" />
                              </div>
                            </>
                          )}
                          {integration.type === 'jira' && (
                            <>
                              <div className="space-y-2">
                                <Label>Jira Site URL</Label>
                                <Input placeholder="https://yourcompany.atlassian.net" />
                              </div>
                              <div className="space-y-2">
                                <Label>API Token</Label>
                                <Input type="password" />
                              </div>
                              <div className="space-y-2">
                                <Label>Project Key</Label>
                                <Input placeholder="SEC" />
                              </div>
                            </>
                          )}
                        </div>
                        <div className="flex justify-end gap-2">
                          <Button variant="outline">Cancel</Button>
                          <Button>Save Changes</Button>
                        </div>
                      </DialogContent>
                    </Dialog>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => handleDisconnect(integration)}
                    >
                      Disconnect
                    </Button>
                  </div>
                </div>
              ) : (
                <Button
                  className="w-full"
                  onClick={() => handleConnect(integration)}
                >
                  Connect {integration.name}
                </Button>
              )}
            </CardContent>
          </Card>
        ))}
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
              Automatically scan repositories on push events and pull requests. Get detailed security
              reports directly in your GitHub checks and comments.
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
