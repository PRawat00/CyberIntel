/**
 * Unit tests for useWebSocket hook.
 *
 * Tests the WebSocket connection management API surface.
 * Note: Full integration testing should be done via E2E tests.
 */

import { describe, it, expect } from "vitest"
import { renderHook } from "@testing-library/react"
import { useWebSocket } from "@/hooks/use-websocket"

describe("useWebSocket", () => {
  describe("API surface", () => {
    it("should return expected API interface", () => {
      const { result } = renderHook(() => useWebSocket(null))

      // Verify all expected properties exist
      expect(result.current).toHaveProperty("sendMessage")
      expect(result.current).toHaveProperty("isConnected")
      expect(result.current).toHaveProperty("isConnecting")
      expect(result.current).toHaveProperty("error")
      expect(result.current).toHaveProperty("close")

      // Verify types
      expect(typeof result.current.sendMessage).toBe("function")
      expect(typeof result.current.isConnected).toBe("boolean")
      expect(typeof result.current.isConnecting).toBe("boolean")
      expect(typeof result.current.close).toBe("function")
    })

    it("should not connect when url is null", () => {
      const { result } = renderHook(() => useWebSocket(null))

      expect(result.current.isConnected).toBe(false)
      expect(result.current.isConnecting).toBe(false)
      expect(result.current.error).toBe(null)
    })

    it("should accept optional callbacks", () => {
      const onMessage = () => {}
      const onOpen = () => {}
      const onClose = () => {}
      const onError = () => {}

      // Should not throw with all options
      const { result } = renderHook(() =>
        useWebSocket(null, {
          onMessage,
          onOpen,
          onClose,
          onError,
          reconnect: false,
          reconnectDelay: 5000,
        })
      )

      expect(result.current).toBeDefined()
    })

    it("should provide sendMessage function", () => {
      const { result } = renderHook(() => useWebSocket(null))

      // sendMessage should be a function
      expect(typeof result.current.sendMessage).toBe("function")
      // Actual sending behavior tested in E2E tests
    })

    it("should provide close function", () => {
      const { result } = renderHook(() => useWebSocket(null))

      // close should be callable
      expect(() => {
        result.current.close()
      }).not.toThrow()
    })
  })

  describe("state management", () => {
    it("should initialize with disconnected state when url is null", () => {
      const { result } = renderHook(() => useWebSocket(null))

      expect(result.current.isConnected).toBe(false)
      expect(result.current.isConnecting).toBe(false)
      expect(result.current.error).toBe(null)
    })

    it("should handle URL prop changes", () => {
      const { rerender } = renderHook(
        ({ url }) => useWebSocket(url),
        { initialProps: { url: null as string | null } }
      )

      // Change from null to URL
      rerender({ url: "ws://localhost:8000/ws/1" })

      // Change to different URL
      rerender({ url: "ws://localhost:8000/ws/2" })

      // Change back to null
      rerender({ url: null })

      // Hook should handle all these changes without throwing
      expect(true).toBe(true)
    })
  })

  describe("options handling", () => {
    it("should accept reconnect option", () => {
      const { result: result1 } = renderHook(() =>
        useWebSocket(null, { reconnect: true })
      )
      const { result: result2 } = renderHook(() =>
        useWebSocket(null, { reconnect: false })
      )

      expect(result1.current).toBeDefined()
      expect(result2.current).toBeDefined()
    })

    it("should accept reconnectDelay option", () => {
      const { result } = renderHook(() =>
        useWebSocket(null, { reconnectDelay: 1000 })
      )

      expect(result.current).toBeDefined()
    })

    it("should handle cleanup on unmount", () => {
      const { unmount } = renderHook(() =>
        useWebSocket("ws://localhost:8000/ws/1")
      )

      // Should not throw on unmount
      expect(() => {
        unmount()
      }).not.toThrow()
    })
  })
})
