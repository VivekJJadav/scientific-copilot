'use client'

import type { Experiment } from '@/lib/types/experiment'

interface ResultsViewerProps {
  experiment: Experiment
}

export function ResultsViewer({ experiment }: ResultsViewerProps) {
  if (!experiment.results && !experiment.error_log) {
    return (
      <div className="rounded-lg border border-[#222222] bg-[#111111] p-6 text-center text-gray-500">
        No results available yet.
      </div>
    )
  }

  return (
    <div className="space-y-4">
      {experiment.results && (
        <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
          <h3 className="mb-3 text-xs font-medium uppercase tracking-wider text-gray-500">Metrics</h3>
          <div className="grid gap-3 sm:grid-cols-2">
            {Object.entries(experiment.results).map(([key, value]) => (
              <div key={key} className="rounded-lg bg-[#0a0a0a] p-3">
                <span className="text-xs text-gray-500">{key}</span>
                <p className="text-lg font-semibold text-white">
                  {typeof value === 'number' ? value.toFixed(4) : value}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      {experiment.result_summary && (
        <div className="rounded-lg border border-[#222222] bg-[#111111] p-4">
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-gray-500">Summary</h3>
          <p className="text-sm text-gray-300">{experiment.result_summary}</p>
        </div>
      )}

      {experiment.error_log && (
        <div className="rounded-lg border border-red-500/20 bg-red-500/5 p-4">
          <h3 className="mb-2 text-xs font-medium uppercase tracking-wider text-red-400">Error Log</h3>
          <pre className="whitespace-pre-wrap text-xs text-red-300 font-mono">{experiment.error_log}</pre>
        </div>
      )}
    </div>
  )
}
