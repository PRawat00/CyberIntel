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
 * Hook to initiate GitHub App installation flow.
 * Returns a function that redirects to GitHub App installation page.
 *
 * Flow:
 * 1. User clicks "Connect GitHub"
 * 2. Redirected to GitHub App installation page where they select repos
 * 3. GitHub redirects back with installation_id and setup_action=install
 * 4. We then initiate OAuth to get user token
 * 5. Callback page saves both installation_id and user token
 */
export function useConnectGitHub() {
  return useMutation({
    mutationFn: async () => {
      // First, get the OAuth auth URL and store state
      const { url: authUrl, state } = await api.getGitHubAuthUrl()
      sessionStorage.setItem("github-oauth-state", state)

      // Now get the GitHub App installation URL
      // After installation, GitHub will redirect to our callback with installation_id
      try {
        const { url: installUrl } = await api.getGitHubInstallUrl()
        // Redirect to GitHub App installation page
        window.location.href = installUrl
      } catch {
        // If App not configured, fall back to regular OAuth
        window.location.href = authUrl
      }
    },
  })
}
