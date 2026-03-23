'use client'

import { useHypotheses } from '@/lib/hooks/useHypotheses'
import { HypothesisList } from '@/components/hypotheses/HypothesisList'
import { TopBar } from '@/components/layout/TopBar'
import { useMapStore } from '@/lib/store/mapStore'
import { generateHypotheses, runAllDebates } from '@/lib/api/hypotheses'
import { toast } from 'sonner'
import { Loader2, Sparkles, Swords } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function HypothesesPage() {
  const isRunning = useMapStore((s) => s.isRunning)
  const setIsRunning = useMapStore((s) => s.setIsRunning)
  const queryClient = useQueryClient()

  const generateMutation = useMutation({
    mutationFn: generateHypotheses,
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      toast.success(`Generated ${data.hypotheses_generated} hypotheses from ${data.gaps_found} gaps`)
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
    onError: () => toast.error('Failed to generate hypotheses'),
    onSettled: () => setIsRunning(false),
  })

  const debateMutation = useMutation({
    mutationFn: runAllDebates,
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      toast.success(`Debated ${data.debated}: ${data.passed} passed, ${data.failed} failed`)
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
    onError: () => toast.error('Failed to run debates'),
    onSettled: () => setIsRunning(false),
  })

  return (
    <div className="flex flex-col">
      <TopBar title="Hypotheses">
        <button
          onClick={() => generateMutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {generateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Sparkles className="h-4 w-4" />}
          Generate Hypotheses
        </button>
        <button
          onClick={() => debateMutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg border border-[#333] bg-[#111111] px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:border-indigo-500/30 hover:text-white disabled:opacity-50"
        >
          {debateMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Swords className="h-4 w-4" />}
          Run All Debates
        </button>
      </TopBar>
      <div className="p-6">
        <HypothesisList />
      </div>
    </div>
  )
}
