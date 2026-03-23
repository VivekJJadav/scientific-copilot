'use client'

import { X, ExternalLink } from 'lucide-react'
import { StatusBadge } from '@/components/shared/StatusBadge'
import { ScoreBadge } from '@/components/shared/ScoreBadge'
import type { Paper } from '@/lib/types/paper'
import type { Hypothesis } from '@/lib/types/hypothesis'
import Link from 'next/link'

interface MapSidebarProps {
  paper?: Paper | null
  hypothesis?: Hypothesis | null
  nodeType: 'paper' | 'hypothesis' | null
  onClose: () => void
}

export function MapSidebar({ paper, hypothesis, nodeType, onClose }: MapSidebarProps) {
  if (!nodeType) return null

  return (
    <div className="fixed right-0 top-0 z-50 h-full w-96 overflow-y-auto border-l border-[#222222] bg-[#0a0a0a] shadow-2xl">
      <div className="flex items-center justify-between border-b border-[#222222] p-4">
        <span className="text-xs font-medium uppercase tracking-wider text-gray-500">
          {nodeType === 'paper' ? 'Paper Details' : 'Hypothesis Details'}
        </span>
        <button onClick={onClose} className="rounded-lg p-1 text-gray-500 hover:bg-[#111111] hover:text-white">
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="space-y-4 p-4">
        {nodeType === 'paper' && paper && (
          <>
            <h2 className="text-base font-semibold text-white">{paper.title}</h2>
            <StatusBadge status={paper.arxiv_status} size="md" />
            <div>
              <h4 className="mb-1 text-xs text-gray-500">Abstract</h4>
              <p className="text-sm text-gray-300 leading-relaxed">{paper.abstract}</p>
            </div>
            <div>
              <h4 className="mb-1 text-xs text-gray-500">Authors</h4>
              <p className="text-sm text-gray-400">
                {paper.authors?.map((a) => a.name).join(', ') || 'Unknown'}
              </p>
            </div>
            <div className="flex items-center gap-2">
              <span className="text-xs text-gray-500">Year: {paper.published_year}</span>
              {paper.pdf_url && (
                <a
                  href={paper.pdf_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="flex items-center gap-1 text-xs text-indigo-400 hover:text-indigo-300"
                >
                  <ExternalLink className="h-3 w-3" />
                  ArXiv
                </a>
              )}
            </div>
          </>
        )}

        {nodeType === 'hypothesis' && hypothesis && (
          <>
            <h2 className="text-base font-semibold text-white">{hypothesis.title}</h2>
            <div className="flex items-center gap-2">
              <StatusBadge status={hypothesis.status} size="md" />
              {hypothesis.iteration_count > 0 && (
                <span className="text-sm text-indigo-400">↻ Iteration {hypothesis.iteration_count}</span>
              )}
            </div>
            <div>
              <h4 className="mb-1 text-xs text-gray-500">Core Claim</h4>
              <p className="text-sm text-gray-300">{hypothesis.core_claim}</p>
            </div>
            <div>
              <h4 className="mb-1 text-xs text-gray-500">Method Sketch</h4>
              <p className="text-sm text-gray-300">{hypothesis.method_sketch}</p>
            </div>
            <div className="flex gap-2">
              <ScoreBadge score={hypothesis.novelty_score} label="Novelty" />
              <ScoreBadge score={hypothesis.feasibility_score} label="Feasibility" />
            </div>
            {hypothesis.risk_factors.length > 0 && (
              <div>
                <h4 className="mb-1 text-xs text-gray-500">Risk Factors</h4>
                <ul className="space-y-1">
                  {hypothesis.risk_factors.map((r, i) => (
                    <li key={i} className="text-xs text-gray-400">• {r}</li>
                  ))}
                </ul>
              </div>
            )}
            {hypothesis.arbiter_notes && (
              <div>
                <h4 className="mb-1 text-xs text-gray-500">Arbiter Notes</h4>
                <p className="text-xs text-gray-400 italic">{hypothesis.arbiter_notes}</p>
              </div>
            )}
            <Link
              href={`/hypotheses/${hypothesis.id}`}
              className="inline-flex items-center gap-1 text-sm text-indigo-400 hover:text-indigo-300"
            >
              View full details →
            </Link>
          </>
        )}
      </div>
    </div>
  )
}
