/**
 * Floating chat button component.
 */

"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { MessageSquare } from "lucide-react"
import { ChatDialog } from "./chat-dialog"

interface ChatButtonProps {
  scanId?: number
}

export function ChatButton({ scanId }: ChatButtonProps) {
  const [open, setOpen] = useState(false)

  return (
    <>
      <Button
        onClick={() => setOpen(true)}
        className="fixed bottom-6 right-6 rounded-full shadow-lg h-14 w-14 z-50"
        size="icon"
        aria-label="Open chat"
      >
        <MessageSquare className="h-6 w-6" />
      </Button>

      <ChatDialog scanId={scanId} open={open} onOpenChange={setOpen} />
    </>
  )
}
