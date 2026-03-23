'use client'

import type { Hypothesis } from '@/lib/types/hypothesis'

interface DebateViewerProps {
  hypothesis: Hypothesis
}

export function DebateViewer({ hypothesis }: DebateViewerProps) {
  const hasDebate = hypothesis.debate_rounds !== null && hypothesis.debate_rounds > 0

  if (!hasDebate) {
    return (
      <div className="rounded-lg border border-[#222222] bg-[#111111] p-6 text-center">
        <p className="text-gray-400">This hypothesis has not been debated yet.</p>
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {/* Proposal */}
      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
        <div className="mb-2 text-xs font-medium text-blue-400">Proposer</div>
        <p className="text-sm text-gray-300">{hypothesis.motivation}</p>
      </div>

      {/* Critic challenges */}
      {hypothesis.risk_factors.length > 0 && (
        <div className="ml-auto max-w-[85%] rounded-lg border border-amber-500/20 bg-amber-500/5 p-4">
          <div className="mb-2 text-xs font-medium text-amber-400">Critic</div>
          <ul className="space-y-1">
            {hypothesis.risk_factors.map((risk, i) => (
              <li key={i} className="text-sm text-gray-300">• {risk}</li>
            ))}
          </ul>
        </div>
      )}

      {/* Rebuttal */}
      <div className="rounded-lg border border-blue-500/20 bg-blue-500/5 p-4">
        <div className="mb-2 text-xs font-medium text-blue-400">Rebuttal — Method Defense</div>
        <p className="text-sm text-gray-300">{hypothesis.method_sketch}</p>
      </div>

      {/* Arbiter verdict */}
      <div
        className={`mx-auto max-w-lg rounded-lg border-2 p-5 text-center ${
          hypothesis.status === 'approved' || hypothesis.status === 'pending'
            ? 'border-green-500/40 bg-green-500/5'
            : 'border-red-500/40 bg-red-500/5'
        }`}
      >
        <div className="mb-2 text-xs font-semibold uppercase tracking-wider text-gray-400">Arbiter Verdict</div>
        <div
          className={`mb-3 text-lg font-bold ${
            hypothesis.status === 'rejected' ? 'text-red-400' : 'text-green-400'
          }`}
        >
          {hypothesis.status === 'rejected' ? 'FAIL' : 'PASS'}
        </div>
        <div className="mb-2 flex justify-center gap-4">
          <span className="text-sm text-gray-400">
            Novelty: <span className="font-medium text-white">{hypothesis.novelty_score.toFixed(2)}</span>
          </span>
          <span className="text-sm text-gray-400">
            Feasibility: <span className="font-medium text-white">{hypothesis.feasibility_score.toFixed(2)}</span>
          </span>
        </div>
        {hypothesis.arbiter_notes && (
          <p className="mt-3 text-xs text-gray-500 italic">&quot;{hypothesis.arbiter_notes}&quot;</p>
        )}
        {hypothesis.rejection_reason && (
          <p className="mt-2 text-xs text-red-400">Rejection: {hypothesis.rejection_reason}</p>
        )}
      </div>
    </div>
  )
}
