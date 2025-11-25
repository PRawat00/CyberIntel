/**
 * React Query hooks for GitHub integration.
 */

import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query"
import { useAuth } from "@/hooks/use-auth"
import { api } from "@/lib/api"

/**
 * Hook to get GitHub connection status.
 */
export function useGitHubConnection() {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["github-connection", user?.id],
    queryFn: () => api.getGitHubConnection(),
    enabled: !!user,
    staleTime: 30000, // 30 seconds
  })
}

/**
 * Hook to list available GitHub repositories.
 */
export function useGitHubRepos() {
  const { user } = useAuth()

  return useQuery({
    queryKey: ["github-repos", user?.id],
    queryFn: () => api.getGitHubRepos(),
    enabled: !!user,
    staleTime: 60000, // 1 minute
  })
}

/**
 * Hook to check if GitHub OAuth is configured.
 */
export function useGitHubOAuthStatus() {
  return useQuery({
    queryKey: ["github-oauth-status"],
    queryFn: () => api.getGitHubOAuthStatus(),
    staleTime: 300000, // 5 minutes
  })
}

/**
 * Mutation hook to set which repository to track.
 */
export function useSetGitHubRepo() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: (repoFullName: string) => api.setGitHubRepo(repoFullName),
    onSuccess: () => {
      // Invalidate connection to refresh repo_full_name
      queryClient.invalidateQueries({ queryKey: ["github-connection", user?.id] })
    },
  })
}

/**
 * Mutation hook to sync GitHub repository.
 */
export function useSyncGitHub() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: () => api.syncGitHub(),
    onSuccess: () => {
      // Invalidate scans list to show new GitHub scans
      queryClient.invalidateQueries({ queryKey: ["scans"] })
      // Update connection status (last_sync_at)
      queryClient.invalidateQueries({ queryKey: ["github-connection", user?.id] })
    },
  })
}

/**
 * Mutation hook to disconnect GitHub.
 */
export function useDisconnectGitHub() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: () => api.disconnectGitHub(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-connection", user?.id] })
      queryClient.invalidateQueries({ queryKey: ["github-repos", user?.id] })
    },
  })
}

/**
 * Mutation hook to toggle auto-sync setting.
 */
export function useToggleGitHubAutoSync() {
  const queryClient = useQueryClient()
  const { user } = useAuth()

  return useMutation({
    mutationFn: () => api.toggleGitHubAutoSync(),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["github-connection", user?.id] })
    },
  })
}

/**
 * Hook to initiate GitHub OAuth flow.
 * Returns a function that redirects to GitHub.
 */
export function useConnectGitHub() {
  const queryClient = useQueryClient()

  return useMutation({
    mutationFn: async () => {
      const { url, state } = await api.getGitHubAuthUrl()
      // Store state in sessionStorage for verification on callback
      sessionStorage.setItem("github-oauth-state", state)
      // Redirect to GitHub
      window.location.href = url
    },
  })
}
