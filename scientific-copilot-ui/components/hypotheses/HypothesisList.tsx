'use client'

import { HypothesisCard } from './HypothesisCard'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'
import { useHypotheses } from '@/lib/hooks/useHypotheses'

export function HypothesisList() {
  const { data, isLoading } = useHypotheses({ limit: 50 })

  if (isLoading) return <LoadingSpinner text="Loading hypotheses..." />
  if (!data?.items.length) return <EmptyState title="No hypotheses yet" description="Generate hypotheses to see them here." />

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      {data.items.map((h) => (
        <HypothesisCard key={h.id} hypothesis={h} />
      ))}
    </div>
  )
}
