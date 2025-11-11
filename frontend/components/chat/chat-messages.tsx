/**
 * Chat messages list component with auto-scroll.
 */

import { useEffect, useRef } from "react"
import { ChatMessage } from "./chat-message"
import { Loader2 } from "lucide-react"
import type { ChatMessage as ChatMessageType } from "@/lib/types"

interface ChatMessagesProps {
  messages: ChatMessageType[] | { role: "user" | "assistant"; content: string }[]
  isLoading?: boolean
  streamingMessage?: { role: "assistant"; content: string } | null
  onRegenerateMessage?: (messageIndex: number) => void
  canRegenerate?: boolean
}

export function ChatMessages({
  messages,
  isLoading = false,
  streamingMessage,
  onRegenerateMessage,
  canRegenerate = true,
}: ChatMessagesProps) {
  const scrollAreaRef = useRef<HTMLDivElement>(null)
  const bottomRef = useRef<HTMLDivElement>(null)

  // Auto-scroll to bottom when new messages arrive (only if user is near bottom)
  useEffect(() => {
    if (scrollAreaRef.current) {
      // Check if user is near the bottom (within 100px)
      const isNearBottom =
        scrollAreaRef.current.scrollHeight -
        scrollAreaRef.current.scrollTop -
        scrollAreaRef.current.clientHeight < 100

      // Only auto-scroll if user is near bottom
      if (isNearBottom) {
        scrollAreaRef.current.scrollTo({
          top: scrollAreaRef.current.scrollHeight,
          behavior: "smooth"
        })
      }
    }
  }, [messages])

  // Auto-scroll for streaming updates (only if user is near bottom)
  useEffect(() => {
    if (scrollAreaRef.current && streamingMessage) {
      // Check if near bottom to avoid disrupting user
      const isNearBottom =
        scrollAreaRef.current.scrollHeight -
        scrollAreaRef.current.scrollTop -
        scrollAreaRef.current.clientHeight < 100

      if (isNearBottom) {
        scrollAreaRef.current.scrollTo({
          top: scrollAreaRef.current.scrollHeight,
          behavior: "auto" // Instant scroll for streaming
        })
      }
    }
  }, [streamingMessage?.content])

  return (
    <div
      ref={scrollAreaRef}
      className="h-full overflow-y-auto overscroll-contain px-4 focus-visible:ring-ring/50 focus-visible:ring-[3px] outline-none rounded-[inherit]"
      style={{
        scrollbarGutter: 'stable',
      }}
      tabIndex={0}
      role="log"
      aria-label="Chat messages"
    >
      <div className="py-4">
        {messages.length === 0 && !isLoading && (
          <div className="flex flex-col items-center justify-center h-full text-center py-12">
            <div className="text-muted-foreground mb-2">
              <svg
                className="w-16 h-16 mx-auto mb-4 opacity-50"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  strokeWidth={2}
                  d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z"
                />
              </svg>
              <p className="text-lg font-medium">Start a conversation</p>
              <p className="text-sm mt-1">
                Ask about vulnerabilities, CVEs, or security best practices
              </p>
            </div>
          </div>
        )}

        {messages.map((message, index) => (
          <ChatMessage
            key={"id" in message ? message.id : index}
            message={message}
            onRegenerate={
              message.role === "assistant" && onRegenerateMessage
                ? () => onRegenerateMessage(index)
                : undefined
            }
            canRegenerate={canRegenerate}
          />
        ))}

        {streamingMessage && (
          <ChatMessage message={streamingMessage} isStreaming />
        )}

        {isLoading && !streamingMessage && (
          <div className="flex items-center gap-2 text-muted-foreground mb-4">
            <Loader2 className="h-4 w-4 animate-spin" />
            <span className="text-sm">Thinking...</span>
          </div>
        )}

        <div ref={bottomRef} />
      </div>
    </div>
  )
}
