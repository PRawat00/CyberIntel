'use client'

import { useState, useEffect } from 'react'
import { X } from 'lucide-react'
import { Badge } from './badge'

export function DemoModeBadge() {
  const [isDemoMode, setIsDemoMode] = useState(false)
  const [isDismissed, setIsDismissed] = useState(false)

  useEffect(() => {
    // Check if demo mode is active
    const checkDemoMode = () => {
      if (typeof window !== 'undefined') {
        setIsDemoMode(!!(window as any).__DEMO_MODE__)
      }
    }

    checkDemoMode()

    // Recheck periodically in case it changes
    const interval = setInterval(checkDemoMode, 2000)
    return () => clearInterval(interval)
  }, [])

  if (!isDemoMode || isDismissed) {
    return null
  }

  return (
    <div className="fixed top-4 right-4 z-[9999] animate-in fade-in slide-in-from-top-2 duration-500">
      <div className="bg-amber-500/90 backdrop-blur-sm text-amber-950 px-4 py-2 rounded-lg shadow-lg border-2 border-amber-600 flex items-center gap-3">
        <div className="flex items-center gap-2">
          <span className="text-xl">🎭</span>
          <div className="flex flex-col">
            <span className="font-bold text-sm leading-tight">DEMO MODE</span>
            <span className="text-xs opacity-90">Using mock data</span>
          </div>
        </div>
        <button
          onClick={() => setIsDismissed(true)}
          className="hover:bg-amber-600/20 rounded p-1 transition-colors"
          aria-label="Dismiss demo mode badge"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="mt-2 text-xs text-center">
        <span className="bg-amber-950/80 text-amber-100 px-2 py-1 rounded text-[10px]">
          Backend not connected
        </span>
      </div>
    </div>
  )
}
