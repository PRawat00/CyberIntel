/**
 * React Query hooks for chat functionality.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { chatApi } from "@/lib/chat-api"

/**
 * Get or create a persistent chat session
 * Uses a single general chat session that persists across all pages
 * Dependency context is managed separately via setContext/clearContext
 */
export function useChatSession() {
  return useQuery({
    queryKey: ["chat-session"],
    queryFn: () => chatApi.getOrCreateSession(undefined),
    enabled: true,
    staleTime: Infinity, // Never refetch automatically
    gcTime: Infinity, // Keep in cache forever
    refetchOnMount: false,
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
}

/**
 * Get messages for a chat session
 * Refetches on mount to ensure fresh data after navigation
 */
export function useChatMessages(sessionId: number | undefined) {
  return useQuery({
    queryKey: ["chat-messages", sessionId],
    queryFn: () => chatApi.getMessages(sessionId!),
    enabled: !!sessionId,
    staleTime: 0, // Always consider stale - refetch when invalidated
    gcTime: Infinity, // Keep in cache forever
    refetchOnMount: true, // Refetch when component mounts (after navigation)
    refetchOnWindowFocus: false,
    refetchOnReconnect: false,
  })
}

/**
 * List all chat sessions, optionally filtered by scan
 */
export function useChatSessions(scanId?: number) {
  return useQuery({
    queryKey: ["chat-sessions", scanId],
    queryFn: () => chatApi.listSessions(scanId),
    staleTime: 5 * 60 * 1000, // 5 minutes
  })
}

/**
 * Create a new chat session
 */
export function useCreateChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: ({ scanId, title }: { scanId?: number; title?: string }) =>
      chatApi.createSession(scanId, title),
    onSuccess: (data) => {
      // Invalidate sessions list
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] })
      // Set the new session in cache
      queryClient.setQueryData(["chat-session", data.scan_id], data)
    },
  })
}

/**
 * Delete a chat session
 */
export function useDeleteChatSession() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: (sessionId: number) => chatApi.deleteSession(sessionId),
    onSuccess: () => {
      // Invalidate all chat-related queries
      queryClient.invalidateQueries({ queryKey: ["chat-sessions"] })
      queryClient.invalidateQueries({ queryKey: ["chat-session"] })
      queryClient.invalidateQueries({ queryKey: ["chat-messages"] })
    },
  })
}
