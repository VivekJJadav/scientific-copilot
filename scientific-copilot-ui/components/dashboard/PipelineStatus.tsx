'use client'

import { clsx } from 'clsx'

interface StatusBar {
  label: string
  count: number
  color: string
}

interface PipelineStatusProps {
  papersByStatus: { raw: number; processed: number; embedded: number }
  hypothesesByStatus: { pending: number; approved: number; rejected: number }
  experimentsByStatus: { queued: number; running: number; completed: number; failed: number }
}

function ProgressBar({ title, bars }: { title: string; bars: StatusBar[] }) {
  const total = bars.reduce((s, b) => s + b.count, 0)
  if (total === 0) {
    return (
      <div className="space-y-1">
        <p className="text-xs text-gray-500">{title}</p>
        <div className="h-3 rounded-full bg-[#1a1a1a]" />
        <div className="flex gap-3 text-xs text-gray-600"><span>No data</span></div>
      </div>
    )
  }

  return (
    <div className="space-y-1">
      <p className="text-xs text-gray-500">{title} ({total})</p>
      <div className="flex h-3 overflow-hidden rounded-full bg-[#1a1a1a]">
        {bars.map(
          (bar) =>
            bar.count > 0 && (
              <div
                key={bar.label}
                className={clsx('h-full transition-all', bar.color)}
                style={{ width: `${(bar.count / total) * 100}%` }}
              />
            )
        )}
      </div>
      <div className="flex flex-wrap gap-3">
        {bars.map((bar) => (
          <span key={bar.label} className="flex items-center gap-1 text-xs text-gray-500">
            <span className={clsx('h-2 w-2 rounded-full', bar.color)} />
            {bar.label}: {bar.count}
          </span>
        ))}
      </div>
    </div>
  )
}

export function PipelineStatus({ papersByStatus, hypothesesByStatus, experimentsByStatus }: PipelineStatusProps) {
  return (
    <div className="space-y-5 rounded-lg border border-[#222222] bg-[#111111] p-4">
      <h3 className="text-sm font-medium text-gray-400">Pipeline Status</h3>
      <ProgressBar
        title="Papers"
        bars={[
          { label: 'Raw', count: papersByStatus.raw, color: 'bg-gray-500' },
          { label: 'Processed', count: papersByStatus.processed, color: 'bg-blue-500' },
          { label: 'Embedded', count: papersByStatus.embedded, color: 'bg-indigo-500' },
        ]}
      />
      <ProgressBar
        title="Hypotheses"
        bars={[
          { label: 'Pending', count: hypothesesByStatus.pending, color: 'bg-amber-500' },
          { label: 'Approved', count: hypothesesByStatus.approved, color: 'bg-green-500' },
          { label: 'Rejected', count: hypothesesByStatus.rejected, color: 'bg-red-500' },
        ]}
      />
      <ProgressBar
        title="Experiments"
        bars={[
          { label: 'Queued', count: experimentsByStatus.queued, color: 'bg-gray-500' },
          { label: 'Running', count: experimentsByStatus.running, color: 'bg-blue-500' },
          { label: 'Completed', count: experimentsByStatus.completed, color: 'bg-green-500' },
          { label: 'Failed', count: experimentsByStatus.failed, color: 'bg-red-500' },
        ]}
      />
    </div>
  )
}
