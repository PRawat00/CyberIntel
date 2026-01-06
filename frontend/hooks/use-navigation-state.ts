import { create } from "zustand"
import { persist } from "zustand/middleware"
import { logger } from "@/lib/logger"

export type NavSection = "dependencies" | "integrations" | "settings"

interface NavigationState {
  // Active L1 section
  activeSection: NavSection

  // Selected scan ID (for dependencies view)
  selectedScanId: number | null

  // L2 sidebar collapsed state
  isL2Collapsed: boolean

  // Actions
  setActiveSection: (section: NavSection) => void
  setSelectedScanId: (id: number | null) => void
  toggleL2Sidebar: () => void
  collapseL2: () => void
  expandL2: () => void
  reset: () => void
}

const initialState = {
  activeSection: "dependencies" as NavSection,
  selectedScanId: null,
  isL2Collapsed: false,
}

export const useNavigationState = create<NavigationState>()(
  persist(
    (set) => ({
      ...initialState,

      setActiveSection: (section) =>
        set({ activeSection: section }),

      setSelectedScanId: (id) => {
        logger.log('[NAVIGATION STATE] setSelectedScanId called:', id)
        set({ selectedScanId: id })
        logger.log('[NAVIGATION STATE] State updated to:', id)
      },

      toggleL2Sidebar: () =>
        set((state) => ({ isL2Collapsed: !state.isL2Collapsed })),

      collapseL2: () =>
        set({ isL2Collapsed: true }),

      expandL2: () =>
        set({ isL2Collapsed: false }),

      reset: () =>
        set(initialState),
    }),
    {
      name: "navigation-state-storage",
      // Only persist selected scan, not UI states
      partialize: (state) => ({
        selectedScanId: state.selectedScanId,
        activeSection: state.activeSection,
      }),
    }
  )
)
