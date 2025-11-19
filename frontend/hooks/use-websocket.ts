/**
 * WebSocket management hook for real-time chat.
 */

import { useEffect, useRef, useState, useCallback } from "react"
import { logger } from "@/lib/logger"
import type { WebSocketMessage } from "@/lib/types"

interface UseWebSocketOptions {
  onMessage?: (message: WebSocketMessage) => void
  onOpen?: () => void
  onClose?: () => void
  onError?: (error: Event) => void
  reconnect?: boolean
  reconnectDelay?: number
}

interface UseWebSocketReturn {
  sendMessage: (content: string, dependencyIds?: number[]) => void
  setContext: (dependencyIds: number[]) => void
  clearContext: () => void
  isConnected: boolean
  isConnecting: boolean
  error: string | null
  close: () => void
}

export function useWebSocket(
  url: string | null,
  options: UseWebSocketOptions = {}
): UseWebSocketReturn {
  const {
    onMessage,
    onOpen,
    onClose,
    onError,
    reconnect = true,
    reconnectDelay = 3000,
  } = options

  const [isConnected, setIsConnected] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  const wsRef = useRef<WebSocket | null>(null)
  const reconnectTimeoutRef = useRef<NodeJS.Timeout | null>(null)
  const reconnectAttemptsRef = useRef(0)
  const mountedRef = useRef(true) // Track if component is mounted

  // Use refs for callbacks to avoid recreating connect function
  const onMessageRef = useRef(onMessage)
  const onOpenRef = useRef(onOpen)
  const onCloseRef = useRef(onClose)
  const onErrorRef = useRef(onError)

  // Update refs when callbacks change
  useEffect(() => {
    onMessageRef.current = onMessage
    onOpenRef.current = onOpen
    onCloseRef.current = onClose
    onErrorRef.current = onError
  }, [onMessage, onOpen, onClose, onError])

  const connect = useCallback(() => {
    if (!url || !mountedRef.current) {
      return
    }

    // If already connected or connecting, don't create new connection
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      logger.log("[WebSocket] Already connected, skipping")
      return
    }

    if (wsRef.current?.readyState === WebSocket.CONNECTING) {
      logger.log("[WebSocket] Already connecting, skipping")
      return
    }

    setIsConnecting(true)
    setError(null)

    try {
      const ws = new WebSocket(url)

      ws.onopen = () => {
        if (!mountedRef.current) return
        logger.log("[WebSocket] Connected")
        setIsConnected(true)
        setIsConnecting(false)
        setError(null)
        reconnectAttemptsRef.current = 0
        onOpenRef.current?.()
      }

      ws.onmessage = (event) => {
        if (!mountedRef.current) return
        try {
          const data = JSON.parse(event.data) as WebSocketMessage
          onMessageRef.current?.(data)
        } catch (err) {
          logger.error("[WebSocket] Failed to parse message:", err)
        }
      }

      ws.onerror = (event) => {
        if (!mountedRef.current) return
        // Note: Browser ErrorEvent objects don't contain detailed error info for security
        logger.log("[WebSocket] Connection error (cosmetic - connection may still work)", {
          readyState: ws.readyState,
          url: url,
          timestamp: new Date().toISOString(),
          eventType: event.type
        })
        setError("WebSocket connection error")
        onErrorRef.current?.(event)
      }

      ws.onclose = (event) => {
        if (!mountedRef.current) return
        logger.log("[WebSocket] Disconnected", {
          code: event.code,
          reason: event.reason,
          wasClean: event.wasClean
        })
        setIsConnected(false)
        setIsConnecting(false)
        wsRef.current = null
        onCloseRef.current?.()

        // Attempt reconnection if enabled and component is still mounted
        if (reconnect && reconnectAttemptsRef.current < 5 && mountedRef.current) {
          reconnectAttemptsRef.current += 1
          logger.log(
            `[WebSocket] Reconnecting... (attempt ${reconnectAttemptsRef.current})`
          )

          reconnectTimeoutRef.current = setTimeout(() => {
            if (mountedRef.current) {
              connect()
            }
          }, reconnectDelay)
        }
      }

      wsRef.current = ws
    } catch (err) {
      logger.error("[WebSocket] Connection failed:", err)
      setError("Failed to connect to chat server")
      setIsConnecting(false)
    }
  }, [url, reconnect, reconnectDelay])

  const sendMessage = useCallback((content: string, dependencyIds?: number[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      const message: any = {
        type: "message",
        content,
      }

      // Add dependency_ids if provided
      if (dependencyIds !== undefined) {
        message.dependency_ids = dependencyIds
      }

      wsRef.current.send(JSON.stringify(message))
    } else {
      logger.warn("[WebSocket] Cannot send message: not connected")
      setError("Not connected to chat server")
    }
  }, [])

  const setContext = useCallback((dependencyIds: number[]) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "set_context",
          dependency_ids: dependencyIds,
        })
      )
    } else {
      logger.warn("[WebSocket] Cannot set context: not connected")
      setError("Not connected to chat server")
    }
  }, [])

  const clearContext = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(
        JSON.stringify({
          type: "clear_context",
        })
      )
    } else {
      logger.warn("[WebSocket] Cannot clear context: not connected")
      setError("Not connected to chat server")
    }
  }, [])

  const close = useCallback(() => {
    logger.log("[WebSocket] Closing connection")
    mountedRef.current = false // Mark as unmounted

    if (reconnectTimeoutRef.current) {
      clearTimeout(reconnectTimeoutRef.current)
      reconnectTimeoutRef.current = null
    }

    if (wsRef.current) {
      wsRef.current.close()
      wsRef.current = null
    }

    setIsConnected(false)
    setIsConnecting(false)
  }, [])

  // Connect on mount if URL is provided
  useEffect(() => {
    mountedRef.current = true

    if (url) {
      logger.log("[WebSocket] URL changed, connecting...", url)
      connect()
    }

    return () => {
      logger.log("[WebSocket] Component unmounting, cleaning up")
      mountedRef.current = false

      if (reconnectTimeoutRef.current) {
        clearTimeout(reconnectTimeoutRef.current)
        reconnectTimeoutRef.current = null
      }

      if (wsRef.current) {
        wsRef.current.close()
        wsRef.current = null
      }
    }
  }, [url, connect])

  return {
    sendMessage,
    setContext,
    clearContext,
    isConnected,
    isConnecting,
    error,
    close,
  }
}
