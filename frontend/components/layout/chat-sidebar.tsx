/**
 * Chat sidebar component - persistent chat interface for dashboard.
 */

"use client"

import { useEffect, useState, useCallback, useMemo } from "react"
import { MessageSquare, XCircle } from "lucide-react"
import { Button } from "@/components/ui/button"
import { ChatMessages } from "@/components/chat/chat-messages"
import { ChatInput } from "@/components/chat/chat-input"
import { useChatSession, useChatMessages } from "@/hooks/use-chat"
import { useWebSocket } from "@/hooks/use-websocket"
import { chatApi } from "@/lib/chat-api"
import { useDependencySelection } from "@/hooks/use-dependency-selection"
import { logger } from "@/lib/logger"
import type { ChatMessage, WebSocketMessage } from "@/lib/types"
import { useQueryClient } from "@tanstack/react-query"

export function ChatSidebar() {
  const queryClient = useQueryClient()
  const { selectedDependencyIds, clearSelection, getSelectedCount } = useDependencySelection()

  const [streamingMessage, setStreamingMessage] = useState<{
    role: "assistant"
    content: string
  } | null>(null)
  const [isWaitingForResponse, setIsWaitingForResponse] = useState(false)
  const [wsUrl, setWsUrl] = useState<string | null>(null)

  // Generate unique temporary IDs using timestamp + random (negative to distinguish from real database IDs)
  const getTempId = useCallback(() => {
    // Multiply by 1000 and add random to ensure uniqueness even if called multiple times in same millisecond
    return -(Date.now() * 1000 + Math.floor(Math.random() * 1000))
  }, [])

  // Get or create persistent chat session (single session for all chats)
  const { data: session } = useChatSession()

  // Get existing messages from React Query cache
  const { data: existingMessages } = useChatMessages(session?.id)

  // Compute display messages (combine cached messages + streaming with deduplication)
  const displayMessages = useMemo(() => {
    let messages = existingMessages || []

    // Deduplication: Remove temporary messages if real version exists from DB
    // Use Map for O(1) lookups instead of array operations
    const realMessages = new Map<string, ChatMessage>()
    const tempMessages: ChatMessage[] = []

    // Single pass: separate real and temporary messages
    for (const msg of messages) {
      const key = `${msg.role}:${msg.content}`

      if (msg.id > 0) {
        // Real message from database - store in map
        realMessages.set(key, msg)
      } else {
        // Temporary optimistic message
        tempMessages.push({ key, msg } as any)
      }
    }

    // Filter temporary messages: only keep if no real version exists
    const deduped = [
      ...realMessages.values(),
      ...tempMessages
        .filter((item: any) => !realMessages.has(item.key))
        .map((item: any) => item.msg)
    ]

    // Add streaming assistant message if exists
    if (streamingMessage && session) {
      return [
        ...deduped,
        {
          id: -999999, // Consistent negative ID for streaming message (temporary)
          session_id: session.id,
          role: streamingMessage.role,
          content: streamingMessage.content,
          created_at: new Date().toISOString(),
        } as ChatMessage,
      ]
    }

    return deduped
  }, [existingMessages, streamingMessage, session])

  // WebSocket message handler
  const handleWebSocketMessage = useCallback(
    (wsMessage: WebSocketMessage) => {
      switch (wsMessage.type) {
        case "start":
          setIsWaitingForResponse(false)
          setStreamingMessage({ role: "assistant", content: "" })
          break

        case "chunk":
          setStreamingMessage((prev) => ({
            role: "assistant",
            content: (prev?.content || "") + (wsMessage.content || ""),
          }))
          break

        case "end":
          // Clear streaming state
          setStreamingMessage(null)

          // Invalidate query to trigger refetch (works for both active and inactive queries)
          if (session) {
            logger.log("[Chat] Invalidating messages after assistant response completed")
            queryClient.invalidateQueries({
              queryKey: ["chat-messages", session.id],
              refetchType: "all", // Refetch both active and inactive queries
            })
          }
          break

        case "error":
          logger.error("[Chat] WebSocket error:", wsMessage.error)
          setIsWaitingForResponse(false)
          setStreamingMessage(null)

          // Add error message to cache
          if (session) {
            const errorMessage: ChatMessage = {
              id: getTempId(), // Use counter for unique temporary ID
              session_id: session.id,
              role: "assistant",
              content: `Sorry, I encountered an error: ${wsMessage.error}`,
              created_at: new Date().toISOString(),
            }
            queryClient.setQueryData(
              ["chat-messages", session.id],
              (old: ChatMessage[] | undefined) => [...(old || []), errorMessage]
            )
          }
          break
      }
    },
    [session, queryClient, getTempId]
  )

  // Resolve WebSocket URL asynchronously when session changes
  useEffect(() => {
    if (session) {
      chatApi.getWebSocketUrl(session.id).then(setWsUrl)
    } else {
      setWsUrl(null)
    }
  }, [session?.id])

  // WebSocket connection
  const { sendMessage, setContext, clearContext: clearWSContext, isConnected } = useWebSocket(
    wsUrl,
    {
      onMessage: handleWebSocketMessage,
      onError: () => {
        logger.log("[Chat] WebSocket error, cleaning up UI state")
        setIsWaitingForResponse(false)
        setStreamingMessage(null)
      },
      onClose: () => {
        logger.log("[Chat] WebSocket closed, cleaning up UI state")
        setIsWaitingForResponse(false)
        setStreamingMessage(null)
      },
    }
  )

  // Send context update when dependency selection changes
  useEffect(() => {
    if (isConnected && session) {
      if (selectedDependencyIds.length > 0) {
        logger.log("[Chat] Updating context with selected dependencies:", selectedDependencyIds)
        setContext(selectedDependencyIds)
      }
    }
  }, [isConnected, session, selectedDependencyIds, setContext])

  // Reset streaming state when connection is lost
  useEffect(() => {
    if (!isConnected) {
      setIsWaitingForResponse(false)
      setStreamingMessage(null)
    }
  }, [isConnected])

  const handleSendMessage = useCallback(
    (content: string) => {
      if (!session) return

      // Optimistically add user message to cache with temporary ID
      const optimisticUserMessage: ChatMessage = {
        id: getTempId(), // Negative ID for temporary messages
        session_id: session.id,
        role: "user",
        content,
        created_at: new Date().toISOString(),
      }

      queryClient.setQueryData(
        ["chat-messages", session.id],
        (old: ChatMessage[] | undefined) => [...(old || []), optimisticUserMessage]
      )

      // Send via WebSocket (backend will check session context for selected dependencies)
      sendMessage(content)

      // Set waiting state
      setIsWaitingForResponse(true)

      // Don't invalidate here - let backend save first
      // Invalidation happens on "end" event after assistant response
    },
    [session, sendMessage, queryClient, getTempId]
  )

  const handleRegenerateMessage = useCallback(
    (messageIndex: number) => {
      if (!session || !existingMessages) return

      // Find the user message that preceded this assistant message
      // Search backwards from the assistant message index to find the user message
      let userMessageContent: string | null = null
      for (let i = messageIndex - 1; i >= 0; i--) {
        if (existingMessages[i].role === "user") {
          userMessageContent = existingMessages[i].content
          break
        }
      }

      if (!userMessageContent) {
        logger.error("Could not find user message to regenerate")
        return
      }

      // Remove the assistant message being regenerated from cache
      queryClient.setQueryData(
        ["chat-messages", session.id],
        (old: ChatMessage[] | undefined) => {
          if (!old) return old
          return old.filter((_, index) => index !== messageIndex)
        }
      )

      // Resend the user message
      sendMessage(userMessageContent)
      setIsWaitingForResponse(true)
    },
    [session, existingMessages, queryClient, sendMessage]
  )

  return (
    <aside className="fixed right-0 top-16 bottom-0 w-[380px] bg-card border-l border-border shadow-xl flex flex-col z-20">
        {/* Header */}
        <div className="flex items-center gap-2 p-4 border-b border-border">
          <MessageSquare className="h-5 w-5 text-primary" />
          <h2 className="font-semibold">Security Assistant</h2>
        </div>

        {/* Connection Status */}
        <div className="px-4 py-2 text-xs text-muted-foreground border-b border-border">
          {isConnected ? (
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-green-500 animate-pulse" />
              Connected
            </span>
          ) : (
            <span className="flex items-center gap-2">
              <span className="h-2 w-2 rounded-full bg-gray-400" />
              Connecting...
            </span>
          )}
        </div>

        {/* Dependency Context Indicator */}
        {getSelectedCount() > 0 && (
          <div className="px-4 py-3 bg-blue-50 dark:bg-blue-950 border-b border-blue-200 dark:border-blue-800">
            <div className="flex items-center justify-between gap-2">
              <div className="flex items-center gap-2 text-sm text-blue-700 dark:text-blue-300">
                <MessageSquare className="h-4 w-4" />
                <span className="font-medium">
                  Focusing on {getSelectedCount()} selected {getSelectedCount() === 1 ? 'dependency' : 'dependencies'}
                </span>
              </div>
              <Button
                variant="ghost"
                size="sm"
                onClick={() => {
                  clearSelection()
                  if (isConnected) {
                    clearWSContext()
                  }
                }}
                className="h-7 px-2 text-blue-700 dark:text-blue-300 hover:text-blue-900 dark:hover:text-blue-100"
              >
                <XCircle className="h-4 w-4 mr-1" />
                Clear
              </Button>
            </div>
            <p className="text-xs text-blue-600 dark:text-blue-400 mt-1">
              AI responses will prioritize these packages
            </p>
          </div>
        )}

        {/* Messages */}
        <div className="flex-1 overflow-hidden min-h-0 h-0">
          <ChatMessages
            messages={displayMessages}
            isLoading={isWaitingForResponse && !streamingMessage}
            onRegenerateMessage={handleRegenerateMessage}
            canRegenerate={!streamingMessage && !isWaitingForResponse}
          />
        </div>

        {/* Input */}
        <div className="border-t border-border">
          <ChatInput
            onSend={handleSendMessage}
            disabled={!session || !isConnected || !!streamingMessage}
            placeholder={
              isConnected ? "Ask about CVEs and security..." : "Connecting..."
            }
          />
        </div>
      </aside>
  )
}
