'use client'

import { useQuery } from '@tanstack/react-query'
import { getReviewQueue } from '@/lib/api/review'
import { ReviewCard } from './ReviewCard'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'
import { EmptyState } from '@/components/shared/EmptyState'

export function ReviewQueue() {
  const { data, isLoading } = useQuery({
    queryKey: ['review-queue'],
    queryFn: getReviewQueue,
    refetchInterval: 30000,
  })

  if (isLoading) return <LoadingSpinner text="Loading review queue..." />
  if (!data?.length) return <EmptyState title="Review queue is empty" description="All hypotheses have been reviewed." />

  return (
    <div className="space-y-4">
      {data.map((item) => (
        <ReviewCard key={item.id} item={item} />
      ))}
    </div>
  )
}
