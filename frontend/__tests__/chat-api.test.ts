/**
 * Unit tests for chat API client.
 *
 * Tests the chat-api.ts client including CRUD operations,
 * error handling, and WebSocket URL generation.
 */

import { describe, it, expect, beforeEach, afterEach, vi } from "vitest"
import { chatApi } from "@/lib/chat-api"
import type { ChatSession, ChatMessage } from "@/lib/types"

describe("chatApi", () => {
  const API_BASE_URL = "http://localhost:8000"

  beforeEach(() => {
    // Clear all mocks before each test
    vi.clearAllMocks()
    // Reset fetch mock
    global.fetch = vi.fn()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  describe("createSession", () => {
    it("should create a general chat session without scan_id", async () => {
      const mockSession: ChatSession = {
        id: 1,
        scan_id: null,
        title: "General Chat",
        session_type: "general",
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 0,
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      })

      const result = await chatApi.createSession()

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scan_id: undefined, title: undefined }),
        }
      )
      expect(result).toEqual(mockSession)
    })

    it("should create a project chat session with scan_id", async () => {
      const mockSession: ChatSession = {
        id: 2,
        scan_id: 42,
        title: "Project Chat",
        session_type: "project",
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 0,
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      })

      const result = await chatApi.createSession(42, "Project Chat")

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions`,
        {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ scan_id: 42, title: "Project Chat" }),
        }
      )
      expect(result).toEqual(mockSession)
    })

    it("should throw error on failed request", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: "Internal Server Error",
        json: async () => ({ error: "Database error" }),
      })

      await expect(chatApi.createSession()).rejects.toThrow("Database error")
    })

    it("should handle error without JSON body", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: "Internal Server Error",
        json: async () => {
          throw new Error("No JSON")
        },
      })

      await expect(chatApi.createSession()).rejects.toThrow(
        "Internal Server Error"
      )
    })
  })

  describe("listSessions", () => {
    it("should list all sessions without filter", async () => {
      const mockSessions: ChatSession[] = [
        {
          id: 1,
          scan_id: null,
          title: "General",
          session_type: "general",
          created_at: "2025-01-09T10:00:00",
          last_message_at: "2025-01-09T10:00:00",
          message_count: 5,
        },
        {
          id: 2,
          scan_id: 42,
          title: "Project",
          session_type: "project",
          created_at: "2025-01-09T11:00:00",
          last_message_at: "2025-01-09T11:00:00",
          message_count: 3,
        },
      ]

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSessions,
      })

      const result = await chatApi.listSessions()

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions`
      )
      expect(result).toEqual(mockSessions)
      expect(result.length).toBe(2)
    })

    it("should list sessions filtered by scan_id", async () => {
      const mockSessions: ChatSession[] = [
        {
          id: 2,
          scan_id: 42,
          title: "Project",
          session_type: "project",
          created_at: "2025-01-09T11:00:00",
          last_message_at: "2025-01-09T11:00:00",
          message_count: 3,
        },
      ]

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSessions,
      })

      const result = await chatApi.listSessions(42)

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions?scan_id=42`
      )
      expect(result).toEqual(mockSessions)
      expect(result[0].scan_id).toBe(42)
    })

    it("should return empty array when no sessions exist", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const result = await chatApi.listSessions()

      expect(result).toEqual([])
    })
  })

  describe("getOrCreateSession", () => {
    it("should return existing session if found", async () => {
      const existingSession: ChatSession = {
        id: 2,
        scan_id: 42,
        title: "Existing",
        session_type: "project",
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 5,
      }

      // Mock listSessions to return existing session
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => [existingSession],
      })

      const result = await chatApi.getOrCreateSession(42)

      expect(result).toEqual(existingSession)
      expect(global.fetch).toHaveBeenCalledTimes(1) // Only called listSessions
    })

    it("should create new session if none exists for scan", async () => {
      const newSession: ChatSession = {
        id: 3,
        scan_id: 42,
        title: null,
        session_type: "project",
        created_at: "2025-01-09T11:00:00",
        last_message_at: "2025-01-09T11:00:00",
        message_count: 0,
      }

      // Mock listSessions to return empty array
      global.fetch = vi
        .fn()
        .mockResolvedValueOnce({
          ok: true,
          json: async () => [],
        })
        // Mock createSession
        .mockResolvedValueOnce({
          ok: true,
          json: async () => newSession,
        })

      const result = await chatApi.getOrCreateSession(42)

      expect(result).toEqual(newSession)
      expect(global.fetch).toHaveBeenCalledTimes(2) // listSessions + createSession
    })

    it("should create general session when no scan_id provided", async () => {
      const generalSession: ChatSession = {
        id: 1,
        scan_id: null,
        title: null,
        session_type: "general",
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 0,
      }

      // When no scan_id, should directly create session
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => generalSession,
      })

      const result = await chatApi.getOrCreateSession()

      expect(result).toEqual(generalSession)
      expect(global.fetch).toHaveBeenCalledTimes(1) // Only createSession
    })
  })

  describe("getSession", () => {
    it("should get a specific session by id", async () => {
      const mockSession: ChatSession = {
        id: 1,
        scan_id: null,
        title: "Test Session",
        session_type: "general",
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 10,
      }

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockSession,
      })

      const result = await chatApi.getSession(1)

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions/1`
      )
      expect(result).toEqual(mockSession)
    })

    it("should throw error if session not found", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: "Not Found",
        json: async () => ({ error: "Session not found" }),
      })

      await expect(chatApi.getSession(999)).rejects.toThrow("Session not found")
    })
  })

  describe("getMessages", () => {
    it("should get messages for a session", async () => {
      const mockMessages: ChatMessage[] = [
        {
          id: 1,
          session_id: 1,
          role: "user",
          content: "Hello",
          context_cves: null,
          created_at: "2025-01-09T10:00:00",
        },
        {
          id: 2,
          session_id: 1,
          role: "assistant",
          content: "Hi there!",
          context_cves: ["CVE-2023-12345"],
          created_at: "2025-01-09T10:01:00",
        },
      ]

      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => mockMessages,
      })

      const result = await chatApi.getMessages(1)

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions/1/messages`
      )
      expect(result).toEqual(mockMessages)
      expect(result.length).toBe(2)
    })

    it("should return empty array when session has no messages", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => [],
      })

      const result = await chatApi.getMessages(1)

      expect(result).toEqual([])
    })

    it("should throw error if session not found", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: "Not Found",
        json: async () => ({ error: "Session not found" }),
      })

      await expect(chatApi.getMessages(999)).rejects.toThrow("Session not found")
    })
  })

  describe("deleteSession", () => {
    it("should delete a session successfully", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: true,
        json: async () => ({ message: "Session deleted" }),
      })

      await chatApi.deleteSession(1)

      expect(global.fetch).toHaveBeenCalledWith(
        `${API_BASE_URL}/api/chat/sessions/1`,
        { method: "DELETE" }
      )
    })

    it("should throw error if session not found", async () => {
      global.fetch = vi.fn().mockResolvedValueOnce({
        ok: false,
        statusText: "Not Found",
        json: async () => ({ error: "Session not found" }),
      })

      await expect(chatApi.deleteSession(999)).rejects.toThrow(
        "Session not found"
      )
    })
  })

  describe("getWebSocketUrl", () => {
    it("should return empty string in SSR environment", () => {
      // Simulate SSR by checking if window is undefined
      const originalWindow = global.window
      // @ts-ignore
      delete global.window

      const result = chatApi.getWebSocketUrl(1)

      expect(result).toBe("")

      // Restore window
      global.window = originalWindow
    })

    it("should generate ws:// URL for http protocol", () => {
      // Mock window.location
      Object.defineProperty(window, "location", {
        value: { protocol: "http:" },
        writable: true,
      })

      const result = chatApi.getWebSocketUrl(1)

      expect(result).toBe("ws://localhost:8000/api/chat/ws/1")
    })

    it("should generate wss:// URL for https protocol", () => {
      // Mock window.location
      Object.defineProperty(window, "location", {
        value: { protocol: "https:" },
        writable: true,
      })

      const result = chatApi.getWebSocketUrl(1)

      // Should use wss:// for https protocol
      expect(result).toMatch(/^wss:\/\//)
      expect(result).toMatch(/\/api\/chat\/ws\/1$/)

      // Restore
      Object.defineProperty(window, "location", {
        value: { protocol: "http:" },
        writable: true,
      })
    })
  })
})
