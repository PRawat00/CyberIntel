/**
 * Sidebar state management hook using Zustand.
 * Manages open/closed state with localStorage persistence.
 */

import { create } from "zustand"
import { persist } from "zustand/middleware"

interface SidebarState {
  isOpen: boolean
  toggle: () => void
  open: () => void
  close: () => void
  reset: () => void
}

export const useSidebar = create<SidebarState>()(
  persist(
    (set) => ({
      isOpen: false, // Always start closed for SSR hydration consistency
      toggle: () => set((state) => ({ isOpen: !state.isOpen })),
      open: () => set({ isOpen: true }),
      close: () => set({ isOpen: false }),
      reset: () => set({ isOpen: false }), // Reset to default state (used during logout)
    }),
    {
      name: "chat-sidebar-storage",
    }
  )
)
