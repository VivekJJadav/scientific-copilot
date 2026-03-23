import { create } from 'zustand'

interface MapState {
  selectedNodeId: string | null
  selectedNodeType: 'paper' | 'hypothesis' | null
  isRunning: boolean
  clusterFilter: string | null
  statusFilter: string | null
  showEdges: boolean
  setSelectedNode: (id: string | null, type: 'paper' | 'hypothesis' | null) => void
  setIsRunning: (running: boolean) => void
  setClusterFilter: (clusterId: string | null) => void
  setStatusFilter: (status: string | null) => void
  toggleEdges: () => void
}

export const useMapStore = create<MapState>((set) => ({
  selectedNodeId: null,
  selectedNodeType: null,
  isRunning: false,
  clusterFilter: null,
  statusFilter: null,
  showEdges: true,
  setSelectedNode: (id, type) => set({ selectedNodeId: id, selectedNodeType: type }),
  setIsRunning: (running) => set({ isRunning: running }),
  setClusterFilter: (clusterId) => set({ clusterFilter: clusterId }),
  setStatusFilter: (status) => set({ statusFilter: status }),
  toggleEdges: () => set((state) => ({ showEdges: !state.showEdges })),
}))
