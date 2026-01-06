"use client"

/**
 * Profile Page
 *
 * User profile page showing account information.
 */

import { useAuth } from '@/hooks/use-auth'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Separator } from '@/components/ui/separator'
import { Badge } from '@/components/ui/badge'
import { useRouter } from 'next/navigation'
import { ArrowLeft, Mail, Calendar, Shield } from 'lucide-react'

export default function ProfilePage() {
  const router = useRouter()
  const { user, loading } = useAuth()

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <p>Loading...</p>
      </div>
    )
  }

  if (!user) {
    router.push('/auth/login')
    return null
  }

  const createdDate = new Date(user.created_at).toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric',
  })

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 p-4">
      <div className="max-w-2xl mx-auto py-12">
        {/* Back Button */}
        <Button
          variant="ghost"
          className="mb-6"
          onClick={() => router.push('/dashboard')}
        >
          <ArrowLeft className="mr-2 h-4 w-4" />
          Back to Dashboard
        </Button>

        {/* Profile Card */}
        <Card>
          <CardHeader>
            <div className="flex items-center gap-4">
              <div className="h-16 w-16 rounded-full bg-primary/10 flex items-center justify-center">
                <span className="text-2xl font-bold">
                  {user.email.charAt(0).toUpperCase()}
                </span>
              </div>
              <div className="flex-1">
                <CardTitle>{user.user_metadata.full_name || 'User'}</CardTitle>
                <CardDescription>{user.email}</CardDescription>
              </div>
              <Badge variant="outline" className="capitalize">
                {user.user_metadata.provider}
              </Badge>
            </div>
          </CardHeader>
          <CardContent className="space-y-6">
            <Separator />

            {/* Account Information */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Account Information</h3>

              <div className="grid gap-4">
                <div className="flex items-start gap-3">
                  <Mail className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Email</p>
                    <p className="text-sm text-muted-foreground">{user.email}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Calendar className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">Member Since</p>
                    <p className="text-sm text-muted-foreground">{createdDate}</p>
                  </div>
                </div>

                <div className="flex items-start gap-3">
                  <Shield className="h-5 w-5 text-muted-foreground mt-0.5" />
                  <div>
                    <p className="text-sm font-medium">User ID</p>
                    <p className="text-sm text-muted-foreground font-mono text-xs">
                      {user.id}
                    </p>
                  </div>
                </div>
              </div>
            </div>

            <Separator />

            {/* Actions */}
            <div className="space-y-4">
              <h3 className="text-lg font-semibold">Actions</h3>

              <div className="flex gap-2">
                <Button variant="outline" disabled>
                  Change Password
                </Button>
                <Button variant="outline" disabled>
                  Delete Account
                </Button>
              </div>
              <p className="text-xs text-muted-foreground">
                Account management features coming soon
              </p>
            </div>
          </CardContent>
        </Card>

        {/* Development Info */}
        {user.user_metadata.provider === 'email' && (
          <Card className="mt-4 bg-muted/50">
            <CardContent className="pt-6">
              <p className="text-xs text-muted-foreground text-center">
                This is a mock auth account for local development. When migrating to Supabase,
                this account will not be transferred.
              </p>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  )
}
