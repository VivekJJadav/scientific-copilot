'use client'

import Link from 'next/link'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ScoreBadge } from '@/components/shared/ScoreBadge'
import type { Hypothesis } from '@/lib/types/hypothesis'

interface HypothesisCardProps {
  hypothesis: Hypothesis
}

export function HypothesisCard({ hypothesis }: HypothesisCardProps) {
  return (
    <Link href={`/hypotheses/${hypothesis.id}`}>
      <div className="group rounded-lg border border-[#222222] bg-[#111111] p-4 transition-colors hover:border-indigo-500/30">
        <div className="mb-2 flex items-center justify-between">
          <StatusBadge status={hypothesis.status} />
          {hypothesis.iteration_count > 0 && (
            <span className="text-xs text-indigo-400">↻ {hypothesis.iteration_count}</span>
          )}
        </div>
        <h3 className="mb-1 line-clamp-2 text-sm font-medium text-gray-200 group-hover:text-white">
          {hypothesis.title}
        </h3>
        <p className="mb-3 line-clamp-2 text-xs text-gray-500">{hypothesis.core_claim}</p>
        <div className="flex items-center gap-2">
          <ScoreBadge score={hypothesis.novelty_score} label="N" />
          <ScoreBadge score={hypothesis.feasibility_score} label="F" />
          {hypothesis.debate_rounds !== null && (
            <span className="text-xs text-gray-600">{hypothesis.debate_rounds} rounds</span>
          )}
        </div>
      </div>
    </Link>
  )
}
