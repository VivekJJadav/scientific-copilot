'use client'

import { ClusterList } from '@/components/clusters/ClusterList'
import { DatasetRegistry } from '@/components/clusters/DatasetRegistry'
import { TopBar } from '@/components/layout/TopBar'
import { useMapStore } from '@/lib/store/mapStore'
import { runClustering } from '@/lib/api/clusters'
import { toast } from 'sonner'
import { Loader2, Network } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function ClustersPage() {
  const isRunning = useMapStore((s) => s.isRunning)
  const setIsRunning = useMapStore((s) => s.setIsRunning)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: runClustering,
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      toast.success(
        `Created ${data.clusters_created} clusters, clustered ${data.papers_clustered} papers, found ${data.datasets_found} datasets`
      )
      queryClient.invalidateQueries({ queryKey: ['clusters'] })
      queryClient.invalidateQueries({ queryKey: ['datasets'] })
    },
    onError: () => toast.error('Failed to run clustering'),
    onSettled: () => setIsRunning(false),
  })

  return (
    <div className="flex flex-col">
      <TopBar title="Paper Clusters">
        <button
          onClick={() => mutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Network className="h-4 w-4" />}
          Run Clustering
        </button>
      </TopBar>
      <div className="space-y-8 p-6">
        <section>
          <h2 className="mb-4 text-sm font-medium text-gray-400">Clusters</h2>
          <ClusterList />
        </section>
        <section>
          <h2 className="mb-4 text-sm font-medium text-gray-400">Datasets</h2>
          <DatasetRegistry />
        </section>
      </div>
    </div>
  )
}
