'use client'

import { TopBar } from '@/components/layout/TopBar'
import { MetricsGrid } from '@/components/dashboard/MetricsGrid'
import { NoveltyChart } from '@/components/dashboard/NoveltyChart'
import { PipelineStatus } from '@/components/dashboard/PipelineStatus'
import { FeedbackMetrics } from '@/components/dashboard/FeedbackMetrics'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { useDashboardMetrics } from '@/lib/hooks/useDashboard'
import { useMapStore } from '@/lib/store/mapStore'
import { runFeedbackLoop } from '@/lib/api/feedback'
import { toast } from 'sonner'
import { Loader2, RefreshCw } from 'lucide-react'
import { useMutation, useQueryClient } from '@tanstack/react-query'

export default function DashboardPage() {
  const { metrics, isLoading } = useDashboardMetrics()
  const isRunning = useMapStore((s) => s.isRunning)
  const setIsRunning = useMapStore((s) => s.setIsRunning)
  const queryClient = useQueryClient()

  const feedbackMutation = useMutation({
    mutationFn: runFeedbackLoop,
    onMutate: () => setIsRunning(true),
    onSuccess: (data) => {
      toast.success(
        `Analyzed ${data.experiments_analyzed} experiments, generated ${data.new_hypotheses_generated} new hypotheses`
      )
      queryClient.invalidateQueries({ queryKey: ['dashboard'] })
      queryClient.invalidateQueries({ queryKey: ['hypotheses'] })
    },
    onError: () => toast.error('Failed to run feedback loop'),
    onSettled: () => setIsRunning(false),
  })

  if (isLoading) return <LoadingSpinner text="Loading dashboard..." />

  return (
    <div className="flex flex-col">
      <TopBar title="Dashboard">
        <button
          onClick={() => feedbackMutation.mutate()}
          disabled={isRunning}
          className="flex items-center gap-2 rounded-lg bg-indigo-600 px-4 py-2 text-sm font-medium text-white transition-colors hover:bg-indigo-500 disabled:opacity-50"
        >
          {feedbackMutation.isPending ? (
            <Loader2 className="h-4 w-4 animate-spin" />
          ) : (
            <RefreshCw className="h-4 w-4" />
          )}
          Run Feedback Loop
        </button>
      </TopBar>
      <div className="space-y-6 p-6">
        <MetricsGrid
          totalPapers={metrics.totalPapers}
          totalHypotheses={metrics.totalHypotheses}
          passedDebate={metrics.passedDebate}
          completedExperiments={metrics.completedExperiments}
          avgNovelty={metrics.avgNovelty}
          maxIteration={metrics.maxIteration}
        />
        <div className="grid gap-6 lg:grid-cols-2">
          <NoveltyChart hypotheses={metrics.hypotheses} />
          <FeedbackMetrics hypotheses={metrics.hypotheses} />
        </div>
        <PipelineStatus
          papersByStatus={metrics.papersByStatus}
          hypothesesByStatus={metrics.hypothesesByStatus}
          experimentsByStatus={metrics.experimentsByStatus}
        />
      </div>
    </div>
  )
}
