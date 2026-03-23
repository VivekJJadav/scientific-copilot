'use client'

import Link from 'next/link'
import { StatusBadge } from '@/components/shared/StatusBadge'
import type { Experiment } from '@/lib/types/experiment'

interface ExperimentCardProps {
  experiment: Experiment
}

export function ExperimentCard({ experiment }: ExperimentCardProps) {
  return (
    <Link href={`/experiments/${experiment.id}`}>
      <div className="group rounded-lg border border-[#222222] bg-[#111111] p-4 transition-colors hover:border-indigo-500/30">
        <div className="mb-2 flex items-center justify-between">
          <StatusBadge status={experiment.status} />
          <span className="text-xs text-gray-600">
            {new Date(experiment.created_at).toLocaleDateString()}
          </span>
        </div>
        <p className="mb-2 text-xs text-gray-500 font-mono truncate">
          {experiment.hypothesis_id}
        </p>
        {experiment.results && (
          <div className="flex flex-wrap gap-2 mt-2">
            {Object.entries(experiment.results).slice(0, 3).map(([key, val]) => (
              <span key={key} className="rounded bg-[#1a1a1a] px-2 py-0.5 text-xs text-gray-400">
                {key}: {typeof val === 'number' ? val.toFixed(2) : val}
              </span>
            ))}
          </div>
        )}
        {experiment.error_log && (
          <p className="mt-2 text-xs text-red-400 line-clamp-2">{experiment.error_log}</p>
        )}
      </div>
    </Link>
  )
}
