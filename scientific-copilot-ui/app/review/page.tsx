'use client'

import { ReviewQueue } from '@/components/review/ReviewQueue'
import { TopBar } from '@/components/layout/TopBar'

export default function ReviewPage() {
  return (
    <div className="flex flex-col">
      <TopBar title="Review Queue" />
      <div className="mx-auto w-full max-w-3xl p-6">
        <ReviewQueue />
      </div>
    </div>
  )
}
