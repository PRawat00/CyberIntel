/**
 * Unit tests for React Query chat hooks.
 *
 * Tests the useChatSession, useChatMessages, useChatSessions,
 * useCreateChatSession, and useDeleteChatSession hooks.
 */

import { describe, it, expect, beforeEach, vi } from "vitest"
import { renderHook, waitFor } from "@testing-library/react"
import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import React, { ReactNode } from "react"
import * as chatApiModule from "@/lib/chat-api"
import {
  useChatSession,
  useChatMessages,
  useChatSessions,
  useCreateChatSession,
  useDeleteChatSession,
} from "@/hooks/use-chat"

// Create a wrapper with QueryClient
function createWrapper() {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
      mutations: {
        retry: false,
      },
    },
  })

  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
  )
}

describe("useChatSession", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should fetch or create a general chat session", async () => {
    const mockSession = {
      id: 1,
      scan_id: null,
      title: "General Chat",
      session_type: "general" as const,
      created_at: "2025-01-09T10:00:00",
      last_message_at: "2025-01-09T10:00:00",
      message_count: 0,
    }

    vi.spyOn(chatApiModule.chatApi, "getOrCreateSession").mockResolvedValue(
      mockSession
    )

    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)

    // Wait for success
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockSession)
    expect(chatApiModule.chatApi.getOrCreateSession).toHaveBeenCalledWith(
      undefined
    )
  })

  it("should handle error when fetching session fails", async () => {
    vi.spyOn(chatApiModule.chatApi, "getOrCreateSession").mockRejectedValue(
      new Error("Failed to fetch session")
    )

    const { result } = renderHook(() => useChatSession(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe("useChatMessages", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should fetch messages for a session", async () => {
    const mockMessages = [
      {
        id: 1,
        session_id: 1,
        role: "user" as const,
        content: "Hello",
        context_cves: null,
        created_at: "2025-01-09T10:00:00",
      },
      {
        id: 2,
        session_id: 1,
        role: "assistant" as const,
        content: "Hi there!",
        context_cves: ["CVE-2023-12345"],
        created_at: "2025-01-09T10:01:00",
      },
    ]

    vi.spyOn(chatApiModule.chatApi, "getMessages").mockResolvedValue(
      mockMessages
    )

    const { result } = renderHook(() => useChatMessages(1), {
      wrapper: createWrapper(),
    })

    // Initially loading
    expect(result.current.isLoading).toBe(true)

    // Wait for success
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockMessages)
    expect(chatApiModule.chatApi.getMessages).toHaveBeenCalledWith(1)
  })

  it("should not fetch when sessionId is undefined", () => {
    vi.spyOn(chatApiModule.chatApi, "getMessages")

    const { result } = renderHook(() => useChatMessages(undefined), {
      wrapper: createWrapper(),
    })

    expect(result.current.isLoading).toBe(false)
    expect(result.current.data).toBeUndefined()
    expect(chatApiModule.chatApi.getMessages).not.toHaveBeenCalled()
  })

  it("should handle error when fetching messages fails", async () => {
    vi.spyOn(chatApiModule.chatApi, "getMessages").mockRejectedValue(
      new Error("Failed to fetch messages")
    )

    const { result } = renderHook(() => useChatMessages(1), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe("useChatSessions", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should fetch all chat sessions", async () => {
    const mockSessions = [
      {
        id: 1,
        scan_id: null,
        title: "General",
        session_type: "general" as const,
        created_at: "2025-01-09T10:00:00",
        last_message_at: "2025-01-09T10:00:00",
        message_count: 5,
      },
      {
        id: 2,
        scan_id: 42,
        title: "Project",
        session_type: "project" as const,
        created_at: "2025-01-09T11:00:00",
        last_message_at: "2025-01-09T11:00:00",
        message_count: 3,
      },
    ]

    vi.spyOn(chatApiModule.chatApi, "listSessions").mockResolvedValue(
      mockSessions
    )

    const { result } = renderHook(() => useChatSessions(), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockSessions)
    expect(chatApiModule.chatApi.listSessions).toHaveBeenCalledWith(undefined)
  })

  it("should fetch sessions filtered by scan_id", async () => {
    const mockSessions = [
      {
        id: 2,
        scan_id: 42,
        title: "Project",
        session_type: "project" as const,
        created_at: "2025-01-09T11:00:00",
        last_message_at: "2025-01-09T11:00:00",
        message_count: 3,
      },
    ]

    vi.spyOn(chatApiModule.chatApi, "listSessions").mockResolvedValue(
      mockSessions
    )

    const { result } = renderHook(() => useChatSessions(42), {
      wrapper: createWrapper(),
    })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockSessions)
    expect(chatApiModule.chatApi.listSessions).toHaveBeenCalledWith(42)
  })
})

describe("useCreateChatSession", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should create a new chat session", async () => {
    const mockNewSession = {
      id: 3,
      scan_id: null,
      title: "New Chat",
      session_type: "general" as const,
      created_at: "2025-01-09T12:00:00",
      last_message_at: "2025-01-09T12:00:00",
      message_count: 0,
    }

    vi.spyOn(chatApiModule.chatApi, "createSession").mockResolvedValue(
      mockNewSession
    )

    const { result } = renderHook(() => useCreateChatSession(), {
      wrapper: createWrapper(),
    })

    // Trigger mutation
    result.current.mutate({ title: "New Chat" })

    // Wait for success
    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockNewSession)
    expect(chatApiModule.chatApi.createSession).toHaveBeenCalledWith(
      undefined,
      "New Chat"
    )
  })

  it("should create a project chat session with scan_id", async () => {
    const mockProjectSession = {
      id: 4,
      scan_id: 42,
      title: "Project Chat",
      session_type: "project" as const,
      created_at: "2025-01-09T12:00:00",
      last_message_at: "2025-01-09T12:00:00",
      message_count: 0,
    }

    vi.spyOn(chatApiModule.chatApi, "createSession").mockResolvedValue(
      mockProjectSession
    )

    const { result } = renderHook(() => useCreateChatSession(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({ scanId: 42, title: "Project Chat" })

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(result.current.data).toEqual(mockProjectSession)
    expect(chatApiModule.chatApi.createSession).toHaveBeenCalledWith(
      42,
      "Project Chat"
    )
  })

  it("should handle error when creation fails", async () => {
    vi.spyOn(chatApiModule.chatApi, "createSession").mockRejectedValue(
      new Error("Failed to create session")
    )

    const { result } = renderHook(() => useCreateChatSession(), {
      wrapper: createWrapper(),
    })

    result.current.mutate({})

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})

describe("useDeleteChatSession", () => {
  beforeEach(() => {
    vi.clearAllMocks()
  })

  it("should delete a chat session", async () => {
    vi.spyOn(chatApiModule.chatApi, "deleteSession").mockResolvedValue(
      undefined
    )

    const { result } = renderHook(() => useDeleteChatSession(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isSuccess).toBe(true))

    expect(chatApiModule.chatApi.deleteSession).toHaveBeenCalledWith(1)
  })

  it("should handle error when deletion fails", async () => {
    vi.spyOn(chatApiModule.chatApi, "deleteSession").mockRejectedValue(
      new Error("Failed to delete session")
    )

    const { result } = renderHook(() => useDeleteChatSession(), {
      wrapper: createWrapper(),
    })

    result.current.mutate(1)

    await waitFor(() => expect(result.current.isError).toBe(true))

    expect(result.current.error).toBeDefined()
  })
})
