/**
 * Chat sidebar toggle button - shows when sidebar is closed.
 */

"use client"

import { MessageSquare } from "lucide-react"
import { Button } from "@/components/ui/button"
import { useSidebar } from "@/hooks/use-sidebar"
import { cn } from "@/lib/utils"

export function ChatSidebarToggle() {
  const { isOpen, open } = useSidebar()

  // Don't show button when sidebar is open
  if (isOpen) return null

  return (
    <Button
      onClick={open}
      className={cn(
        "fixed bottom-6 right-6 z-40",
        "h-14 w-14 rounded-full shadow-lg",
        "transition-transform hover:scale-110"
      )}
      size="icon"
      aria-label="Open chat"
    >
      <MessageSquare className="h-6 w-6" />
    </Button>
  )
}
