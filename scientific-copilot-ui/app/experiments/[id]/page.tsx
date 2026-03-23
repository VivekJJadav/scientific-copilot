'use client'

import { use } from 'react'
import { useExperiment } from '@/lib/hooks/useExperiments'
import { TopBar } from '@/components/layout/TopBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ResultsViewer } from '@/components/experiments/ResultsViewer'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export default function ExperimentDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: experiment, isLoading } = useExperiment(id)

  if (isLoading) return <LoadingSpinner text="Loading experiment..." />
  if (!experiment) return <div className="p-6 text-gray-400">Experiment not found.</div>

  return (
    <div className="flex flex-col">
      <TopBar title="Experiment Detail" />
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        <div className="rounded-lg border border-[#222222] bg-[#111111] p-6">
          <div className="mb-3 flex items-center gap-3">
            <StatusBadge status={experiment.status} size="md" />
            {experiment.started_at && (
              <span className="text-xs text-gray-500">
                Started: {new Date(experiment.started_at).toLocaleString()}
              </span>
            )}
          </div>
          <p className="mb-1 text-xs text-gray-500">Experiment ID</p>
          <p className="mb-3 font-mono text-sm text-gray-300">{experiment.id}</p>
          <p className="mb-1 text-xs text-gray-500">Hypothesis ID</p>
          <p className="font-mono text-sm text-indigo-400">{experiment.hypothesis_id}</p>
        </div>

        <ResultsViewer experiment={experiment} />
      </div>
    </div>
  )
}
