"use client"

/**
 * Auth Loading Page
 *
 * Provides a 3-second buffer between login and protected pages
 * to ensure authentication state is fully settled before navigation.
 */

import { Suspense, useEffect, useState } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import CounterLoader from '@/components/ui/counter-loader'

function LoadingPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [countdown, setCountdown] = useState(3)

  // Get the intended destination from query params, default to /dashboard
  const redirect = searchParams.get('redirect') || '/dashboard'

  useEffect(() => {
    console.log('🔐 Auth loading page mounted, redirecting to:', redirect)
    console.log('🔐 Countdown starting from 3 seconds...')

    // Start countdown timer
    const countdownInterval = setInterval(() => {
      setCountdown((prev) => {
        if (prev <= 1) {
          clearInterval(countdownInterval)
          console.log('🔐 Countdown complete, navigating to:', redirect)
          // Navigate to the intended destination
          router.push(redirect)
          return 0
        }
        return prev - 1
      })
    }, 1000)

    // Cleanup on unmount
    return () => {
      clearInterval(countdownInterval)
    }
  }, [redirect, router])

  return (
    <div className="min-h-screen flex flex-col items-center justify-center bg-gradient-to-b from-background to-muted/20">
      <motion.div
        initial={{ opacity: 0, scale: 0.95 }}
        animate={{ opacity: 1, scale: 1 }}
        transition={{ duration: 0.3 }}
        className="text-center space-y-8 px-4"
      >
        {/* Loading Spinner */}
        <div className="relative w-24 h-24 mx-auto">
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-primary/20"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "linear",
            }}
          />
          <motion.div
            className="absolute inset-0 rounded-full border-4 border-transparent border-t-primary"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 1,
              repeat: Infinity,
              ease: "linear",
            }}
          />

          {/* Countdown number in center */}
          <div className="absolute inset-0 flex items-center justify-center">
            <motion.span
              key={countdown}
              initial={{ scale: 0.8, opacity: 0 }}
              animate={{ scale: 1, opacity: 1 }}
              exit={{ scale: 1.2, opacity: 0 }}
              className="text-3xl font-bold text-primary"
            >
              {countdown}
            </motion.span>
          </div>
        </div>

        {/* Status Text */}
        <div className="space-y-2">
          <motion.h1
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.1 }}
            className="text-2xl font-semibold"
          >
            Preparing Your Experience
          </motion.h1>
          <motion.p
            initial={{ y: 10, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ delay: 0.2 }}
            className="text-muted-foreground"
          >
            Setting up your session...
          </motion.p>
        </div>

        {/* Progress Dots */}
        <div className="flex gap-2 justify-center">
          {[0, 1, 2].map((index) => (
            <motion.div
              key={index}
              className="w-2 h-2 rounded-full bg-primary/30"
              animate={{
                scale: countdown === 3 - index ? 1.5 : 1,
                backgroundColor: countdown === 3 - index
                  ? "hsl(var(--primary))"
                  : "hsl(var(--primary) / 0.3)",
              }}
              transition={{
                duration: 0.3,
              }}
            />
          ))}
        </div>

        {/* Debug Info (only in development) */}
        {process.env.NODE_ENV === 'development' && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.5 }}
            className="mt-8 text-xs text-muted-foreground font-mono"
          >
            Redirecting to: {redirect}
          </motion.div>
        )}
      </motion.div>
    </div>
  )
}

export default function AuthLoadingPage() {
  return (
    <Suspense fallback={<CounterLoader />}>
      <LoadingPageContent />
    </Suspense>
  )
}
