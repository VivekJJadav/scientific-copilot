'use client'

import { use } from 'react'
import { useHypothesis } from '@/lib/hooks/useHypotheses'
import { TopBar } from '@/components/layout/TopBar'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ScoreBadge } from '@/components/shared/ScoreBadge'
import { DebateViewer } from '@/components/hypotheses/DebateViewer'
import { LoadingSpinner } from '@/components/shared/LoadingSpinner'

export default function HypothesisDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params)
  const { data: hypothesis, isLoading } = useHypothesis(id)

  if (isLoading) return <LoadingSpinner text="Loading hypothesis..." />
  if (!hypothesis) return <div className="p-6 text-gray-400">Hypothesis not found.</div>

  return (
    <div className="flex flex-col">
      <TopBar title="Hypothesis Detail" />
      <div className="mx-auto max-w-4xl space-y-6 p-6">
        {/* Header */}
        <div className="rounded-lg border border-[#222222] bg-[#111111] p-6">
          <div className="mb-3 flex items-center gap-3">
            <StatusBadge status={hypothesis.status} size="md" />
            {hypothesis.iteration_count > 0 && (
              <span className="rounded-full bg-indigo-500/20 px-3 py-1 text-sm font-medium text-indigo-400">
                ↻ Iteration {hypothesis.iteration_count}
              </span>
            )}
          </div>
          <h2 className="mb-2 text-xl font-semibold text-white">{hypothesis.title}</h2>
          <p className="text-sm text-gray-400">{hypothesis.core_claim}</p>
          <div className="mt-4 flex gap-3">
            <ScoreBadge score={hypothesis.novelty_score} label="Novelty" />
            <ScoreBadge score={hypothesis.feasibility_score} label="Feasibility" />
          </div>
        </div>

        {/* Details grid */}
        <div className="grid gap-4 md:grid-cols-2">
          <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Motivation</h3>
            <p className="text-sm text-gray-300">{hypothesis.motivation}</p>
          </div>
          <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Method Sketch</h3>
            <p className="text-sm text-gray-300">{hypothesis.method_sketch}</p>
          </div>
          <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Expected Outcome</h3>
            <p className="text-sm text-gray-300">{hypothesis.expected_outcome}</p>
          </div>
          <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Gap Description</h3>
            <p className="text-sm text-gray-300">{hypothesis.gap_description}</p>
          </div>
        </div>

        {/* Risk factors */}
        {hypothesis.risk_factors.length > 0 && (
          <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
            <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Risk Factors</h3>
            <ul className="space-y-1">
              {hypothesis.risk_factors.map((r, i) => (
                <li key={i} className="flex items-start gap-2 text-sm text-gray-300">
                  <span className="mt-1 h-1.5 w-1.5 flex-shrink-0 rounded-full bg-amber-400" />
                  {r}
                </li>
              ))}
            </ul>
          </div>
        )}

        {/* Debate transcript */}
        <div>
          <h3 className="mb-3 text-sm font-medium text-gray-400">Debate Transcript</h3>
          <DebateViewer hypothesis={hypothesis} />
        </div>
      </div>
    </div>
  )
}
