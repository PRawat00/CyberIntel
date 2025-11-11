/**
 * Login Page
 *
 * Sign in page with email/password form and OAuth buttons.
 */

import Link from 'next/link'
import { LoginForm } from '@/components/auth/login-form'
import { SocialAuthButtons } from '@/components/auth/social-auth-buttons'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Separator } from '@/components/ui/separator'
import { Shield } from 'lucide-react'

export default function LoginPage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-background via-background to-muted/20 p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="flex items-center justify-center mb-8">
          <Link href="/" className="flex items-center gap-2 text-2xl font-bold">
            <Shield className="h-8 w-8 text-primary" />
            <span>CyberIntel</span>
          </Link>
        </div>

        {/* Login Card */}
        <Card>
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center">Sign in</CardTitle>
            <CardDescription className="text-center">
              Enter your email and password to sign in to your account
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Email/Password Form */}
            <LoginForm />

            {/* Divider */}
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <Separator />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-card px-2 text-muted-foreground">
                  Or continue with
                </span>
              </div>
            </div>

            {/* OAuth Buttons */}
            <SocialAuthButtons />

            {/* Sign Up Link */}
            <p className="text-center text-sm text-muted-foreground">
              Don't have an account?{' '}
              <Link
                href="/auth/signup"
                className="font-medium text-primary hover:underline"
              >
                Sign up
              </Link>
            </p>
          </CardContent>
        </Card>

        {/* Test Credentials */}
        <Card className="mt-4 bg-muted/50">
          <CardContent className="pt-6">
            <p className="text-xs text-muted-foreground text-center mb-2">
              <strong>Test Credentials:</strong>
            </p>
            <div className="space-y-1 text-xs text-muted-foreground">
              <p className="text-center">Email: <code>local@test.dev</code></p>
              <p className="text-center">Password: <code>password123</code></p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
