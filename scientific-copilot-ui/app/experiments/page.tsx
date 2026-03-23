'use client'

import { ExperimentList } from '@/components/experiments/ExperimentList'
import { TopBar } from '@/components/layout/TopBar'
import { useMapStore } from '@/lib/store/mapStore'
import { runExperiments } from '@/lib/api/experiments'
import { toast } from 'sonner'
import { Loader2, Play } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function ExperimentsPage() {
  const isRunning = useMapStore((s) => s.isRunning)
  const setIsRunning = useMapStore((s) => s.setIsRunning)
  const queryClient = useQueryClient()

  const mutation = useMutation({
    mutationFn: runExperiments,
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      toast.success(`Ran ${data.ran} experiments: ${data.completed} completed, ${data.failed} failed`)
      queryClient.invalidateQueries({ queryKey: ['experiments'] })
    },
    onError: () => toast.error('Failed to run experiments'),
    onSettled: () => setIsRunning(false),
  })

  return (
    <div className="flex flex-col">
      <TopBar title="Experiments">
        <button
          onClick={() => mutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {mutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Play className="h-4 w-4" />}
          Run Experiments
        </button>
      </TopBar>
      <div className="p-6">
        <ExperimentList />
      </div>
    </div>
  )
}
