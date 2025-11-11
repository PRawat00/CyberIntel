/**
 * Main chat dialog component with WebSocket integration.
 */

"use client"

import { useState, useEffect, useCallback } from "react"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { ChatMessages } from "./chat-messages"
import { ChatInput } from "./chat-input"
import { useChatSession, useChatMessages } from "@/hooks/use-chat"
import { useWebSocket } from "@/hooks/use-websocket"
import { chatApi } from "@/lib/chat-api"
import { AlertCircle, Wifi, WifiOff } from "lucide-react"
import type { ChatMessage, WebSocketMessage } from "@/lib/types"

interface ChatDialogProps {
  scanId?: number
  open: boolean
  onOpenChange: (open: boolean) => void
}

export function ChatDialog({ scanId, open, onOpenChange }: ChatDialogProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([])
  const [streamingMessage, setStreamingMessage] = useState<{
    role: "assistant"
    content: string
  } | null>(null)

  // Get or create chat session (single persistent session)
  const { data: session, isLoading: sessionLoading } = useChatSession()

  // Get existing messages
  const { data: existingMessages } = useChatMessages(session?.id)

  // Initialize messages from API
  useEffect(() => {
    if (existingMessages) {
      setMessages(existingMessages)
    }
  }, [existingMessages])

  // WebSocket connection
  const handleWebSocketMessage = useCallback((wsMessage: WebSocketMessage) => {
    switch (wsMessage.type) {
      case "start":
        // Initialize streaming message
        setStreamingMessage({ role: "assistant", content: "" })
        break

      case "chunk":
        // Append chunk to streaming message
        setStreamingMessage((prev) => ({
          role: "assistant",
          content: (prev?.content || "") + (wsMessage.content || ""),
        }))
        break

      case "end":
        // Finalize message
        if (streamingMessage) {
          const finalMessage: ChatMessage = {
            id: wsMessage.message_id!,
            session_id: session!.id,
            role: "assistant",
            content: streamingMessage.content,
            created_at: new Date().toISOString(),
          }
          setMessages((prev) => [...prev, finalMessage])
        }
        setStreamingMessage(null)
        break

      case "error":
        console.error("[Chat] WebSocket error:", wsMessage.error)
        setStreamingMessage(null)
        break
    }
  }, [streamingMessage, session])

  const { sendMessage, isConnected, isConnecting, error: wsError } = useWebSocket(
    session ? chatApi.getWebSocketUrl(session.id) : null,
    {
      onMessage: handleWebSocketMessage,
    }
  )

  const handleSendMessage = (content: string) => {
    // Add user message immediately
    const userMessage: ChatMessage = {
      id: Date.now(), // Temporary ID
      session_id: session!.id,
      role: "user",
      content,
      created_at: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, userMessage])

    // Send via WebSocket (backend will check session context for selected dependencies)
    sendMessage(content)
  }

  const isReady = session && isConnected && !sessionLoading

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl h-[85vh] flex flex-col p-0">
        <DialogHeader className="px-6 pt-6 pb-4 border-b">
          <DialogTitle className="flex items-center gap-2">
            Chat Assistant
            {isConnected ? (
              <Wifi className="h-4 w-4 text-green-500" />
            ) : (
              <WifiOff className="h-4 w-4 text-muted-foreground" />
            )}
          </DialogTitle>
          <DialogDescription>
            {scanId
              ? "Ask questions about vulnerabilities in this scan"
              : "Ask general questions about CVEs and security"}
          </DialogDescription>
        </DialogHeader>

        {/* Connection Status / Errors */}
        {wsError && (
          <div className="px-6 pt-4">
            <Alert variant="destructive">
              <AlertCircle className="h-4 w-4" />
              <AlertDescription>{wsError}</AlertDescription>
            </Alert>
          </div>
        )}

        {isConnecting && (
          <div className="px-6 pt-4">
            <Alert>
              <AlertDescription>Connecting to chat server...</AlertDescription>
            </Alert>
          </div>
        )}

        {/* Messages */}
        <ChatMessages
          messages={messages}
          isLoading={sessionLoading}
          streamingMessage={streamingMessage}
        />

        {/* Input */}
        <ChatInput
          onSend={handleSendMessage}
          disabled={!isReady || !!streamingMessage}
          placeholder={
            isReady
              ? "Ask about vulnerabilities..."
              : "Connecting to chat..."
          }
        />
      </DialogContent>
    </Dialog>
  )
}
