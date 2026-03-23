'use client'

import { ExperimentCard } from './ExperimentCard'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { useExperiments } from '@/lib/hooks/useExperiments'

export function ExperimentList() {
  const { data, isLoading } = useExperiments()

  if (isLoading) return <LoadingSpinner text="Loading experiments..." />
  if (!data?.items.length) return <EmptyState title="No experiments yet" description="Approve a hypothesis and run experiments to see them here." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.items.map((e) => (
        <ExperimentCard key={e.id} experiment={e} />
      ))}
    </div>
  )
}
