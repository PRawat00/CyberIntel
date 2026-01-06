import { create } from "zustand"

interface DependencySelectionState {
  selectedDependencyIds: number[]
  scanId: number | null

  // Actions
  selectDependency: (depId: number, scanId: number) => void
  deselectDependency: (depId: number) => void
  toggleDependency: (depId: number, scanId: number) => void
  clearSelection: () => void
  setSelection: (depIds: number[], scanId: number) => void

  // Queries
  isSelected: (depId: number) => boolean
  getSelectedCount: () => number
  hasSelection: () => boolean
}

export const useDependencySelection = create<DependencySelectionState>()((set, get) => ({
  selectedDependencyIds: [],
  scanId: null,

  selectDependency: (depId, scanId) =>
    set((state) => {
      // If switching to a different scan, clear previous selection
      if (state.scanId !== null && state.scanId !== scanId) {
        return {
          selectedDependencyIds: [depId],
          scanId: scanId,
        }
      }

      // Add to existing selection if not already selected
      if (!state.selectedDependencyIds.includes(depId)) {
        return {
          selectedDependencyIds: [...state.selectedDependencyIds, depId],
          scanId: scanId,
        }
      }

      return state
    }),

  deselectDependency: (depId) =>
    set((state) => ({
      selectedDependencyIds: state.selectedDependencyIds.filter(
        (id) => id !== depId
      ),
    })),

  toggleDependency: (depId, scanId) => {
    const { isSelected, selectDependency, deselectDependency } = get()
    if (isSelected(depId)) {
      deselectDependency(depId)
    } else {
      selectDependency(depId, scanId)
    }
  },

  clearSelection: () =>
    set({
      selectedDependencyIds: [],
      scanId: null,
    }),

  setSelection: (depIds, scanId) =>
    set({
      selectedDependencyIds: depIds,
      scanId: scanId,
    }),

  isSelected: (depId) => get().selectedDependencyIds.includes(depId),

  getSelectedCount: () => get().selectedDependencyIds.length,

  hasSelection: () => get().selectedDependencyIds.length > 0,
}))
