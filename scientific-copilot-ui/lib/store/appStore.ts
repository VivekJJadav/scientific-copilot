import { create } from 'zustand'

export type DrawerType = 'review' | 'debate' | 'detail' | 'experiment' | 'dashboard' | 'feedback' | null

export interface SelectedNode {
  id: string
  type: 'paper' | 'hypothesis'
}

interface AppStore {
  selectedNode: SelectedNode | null
  openDrawer: DrawerType
  drawerData: Record<string, unknown>
  isRunning: boolean
  runningStage: string | null
  newHypothesisIds: string[]

  setSelectedNode: (node: SelectedNode | null) => void
  openDrawerWith: (drawer: DrawerType, data?: Record<string, unknown>) => void
  closeDrawer: () => void
  setRunning: (running: boolean, stage?: string) => void
  addNewHypothesisId: (id: string) => void
  clearNewHypothesisIds: () => void
}

export const useAppStore = create<AppStore>((set) => ({
  selectedNode: null,
  openDrawer: null,
  drawerData: {},
  isRunning: false,
  runningStage: null,
  newHypothesisIds: [],

  setSelectedNode: (node) =>
    set({ selectedNode: node }),

  openDrawerWith: (drawer, data = {}) =>
    set({ openDrawer: drawer, drawerData: data }),

  closeDrawer: () =>
    set({ openDrawer: null, drawerData: {} }),

  setRunning: (running, stage) =>
    set({ isRunning: running, runningStage: running ? (stage ?? null) : null }),

  addNewHypothesisId: (id) =>
    set((state) => ({
      newHypothesisIds: [...state.newHypothesisIds, id],
    })),

  clearNewHypothesisIds: () =>
    set({ newHypothesisIds: [] }),
}))
