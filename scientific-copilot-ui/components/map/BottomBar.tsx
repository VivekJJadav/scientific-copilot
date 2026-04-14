'use client'

import { usePipelineState } from '@/lib/hooks/usePipelineState'
import { useAppStore } from '@/lib/store/appStore'

export function BottomBar() {
  const { counts } = usePipelineState()
  const { openDrawerWith, isRunning } = useAppStore()

  const stats = [
    { label: 'PAPERS', value: counts.papers, color: '#00d4ff' },
    { label: 'CLUSTERS', value: counts.clusters, color: '#00e5a0' },
    { label: 'HYP', value: counts.hypotheses, color: '#a78bfa' },
    { label: 'EXP', value: counts.experiments, color: '#ffb224' },
    { label: 'CYCLE', value: counts.maxIteration, color: '#00d4ff' },
  ]

  return (
    <button
      onClick={() => openDrawerWith('dashboard')}
      className="relative h-9 w-full bg-surface border-t border-border flex items-center justify-center gap-8 px-4 shrink-0 z-40 cursor-pointer hover:bg-panel transition-colors overflow-hidden"
    >
      {/* Scan line when running */}
      {isRunning && <div className="scan-line-overlay" />}

      {stats.map((stat, i) => (
        <div key={stat.label} className="flex items-center gap-2">
          <span className="text-[8px] font-mono tracking-[0.12em] text-text-muted">{stat.label}</span>
          <span
            className="text-[10px] font-mono font-semibold tabular-nums"
            style={{ color: stat.color }}
          >
            {stat.value}
          </span>
          {i < stats.length - 1 && (
            <span className="text-text-muted/30 text-[8px] ml-2">│</span>
          )}
        </div>
      ))}
    </button>
  )
}
