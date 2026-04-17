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
  taskProgress: number
  taskMessage: string | null
  newHypothesisIds: string[]
  ingestLimit: number

  setSelectedNode: (node: SelectedNode | null) => void
  openDrawerWith: (drawer: DrawerType, data?: Record<string, unknown>) => void
  closeDrawer: () => void
  setRunning: (running: boolean, stage?: string) => void
  setTaskProgress: (progress: number, message?: string | null) => void
  addNewHypothesisId: (id: string) => void
  clearNewHypothesisIds: () => void
  setIngestLimit: (limit: number) => void
}

export const useAppStore = create<AppStore>((set) => ({
  selectedNode: null,
  openDrawer: null,
  drawerData: {},
  isRunning: false,
  runningStage: null,
  taskProgress: 0,
  taskMessage: null,
  newHypothesisIds: [],
  ingestLimit: 2,

  setSelectedNode: (node) =>
    set({ selectedNode: node }),

  openDrawerWith: (drawer, data = {}) =>
    set({ openDrawer: drawer, drawerData: data }),

  closeDrawer: () =>
    set({ openDrawer: null, drawerData: {} }),

  setRunning: (running, stage) =>
    set({
      isRunning: running,
      runningStage: running ? (stage ?? null) : null,
      taskProgress: running ? 0 : 0,
      taskMessage: running ? 'Queued' : null,
    }),

  setTaskProgress: (progress, message = null) =>
    set({ taskProgress: progress, taskMessage: message }),

  addNewHypothesisId: (id) =>
    set((state) => ({
      newHypothesisIds: [...state.newHypothesisIds, id],
    })),

  clearNewHypothesisIds: () =>
    set({ newHypothesisIds: [] }),

  setIngestLimit: (limit) =>
    set({ ingestLimit: limit }),
}))
