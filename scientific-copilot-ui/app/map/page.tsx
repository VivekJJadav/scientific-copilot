'use client'

import { ResearchMap } from '@/components/map/ResearchMap'
import { TopBar } from '@/components/layout/TopBar'
import { useMapStore } from '@/lib/store/mapStore'
import { ingestPapers } from '@/lib/api/papers'
import { runExtraction } from '@/lib/api/hypotheses'
import { toast } from 'sonner'
import { Loader2, Download, Cpu } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function MapPage() {
  const isRunning = useMapStore((s: any) => s.isRunning)
  const setIsRunning = useMapStore((s: any) => s.setIsRunning)
  const queryClient = useQueryClient()

  const ingestMutation = useMutation({
    mutationFn: ingestPapers,
    onMutate: () => setIsRunning(true),
    onSuccess: (data: any) => {
      toast.success(`Fetched ${data.fetched} papers: ${data.inserted} new, ${data.skipped} skipped`)
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
    onError: () => toast.error('Failed to ingest papers'),
    onSettled: () => setIsRunning(false),
  })

  const extractMutation = useMutation({
    mutationFn: runExtraction,
    onMutate: () => setIsRunning(true),
    onSuccess: (data: any) => {
      toast.success(`Processed ${data.processed}, embedded ${data.embedded}`)
      queryClient.invalidateQueries({ queryKey: ['papers'] })
    },
    onError: () => toast.error('Failed to extract papers'),
    onSettled: () => setIsRunning(false),
  })

  return (
    <div className="flex h-screen flex-col">
      <TopBar title="Research Map">
        <button
          onClick={() => ingestMutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {ingestMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Download className="h-4 w-4" />}
          Run Ingestion
        </button>
        <button
          onClick={() => extractMutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg border border-[#333] bg-[#111111] px-4 py-2 text-sm font-medium text-gray-300 transition-colors hover:border-indigo-500/30 hover:text-white disabled:opacity-50"
        >
          {extractMutation.isPending ? <Loader2 className="h-4 w-4 animate-spin" /> : <Cpu className="h-4 w-4" />}
          Extract & Embed
        </button>
      </TopBar>
      <div className="flex-1">
        <ResearchMap />
      </div>
    </div>
  )
}
