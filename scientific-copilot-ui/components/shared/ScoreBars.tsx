'use client'

interface ScoreBarsProps {
  novelty: number
  feasibility: number
}

function getScoreColor(score: number, type: 'novelty' | 'feasibility'): string {
  if (type === 'novelty') {
    if (score >= 0.7) return '#a78bfa'
    if (score >= 0.5) return '#ffb224'
    return '#ff3b5c'
  }
  if (score >= 0.7) return '#00e5a0'
  if (score >= 0.5) return '#ffb224'
  return '#ff3b5c'
}

export function ScoreBars({ novelty, feasibility }: ScoreBarsProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center gap-2">
        <span className="text-[8px] font-mono uppercase tracking-widest text-text-secondary w-16">novelty</span>
        <div className="flex-1 h-[3px] bg-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full animate-fill-bar"
            style={{
              width: `${novelty * 100}%`,
              backgroundColor: getScoreColor(novelty, 'novelty'),
              boxShadow: `0 0 6px ${getScoreColor(novelty, 'novelty')}40`,
            }}
          />
        </div>
        <span className="text-[9px] font-mono text-text-secondary w-7 text-right tabular-nums">{novelty.toFixed(2)}</span>
      </div>
      <div className="flex items-center gap-2">
        <span className="text-[8px] font-mono uppercase tracking-widest text-text-secondary w-16">feasib.</span>
        <div className="flex-1 h-[3px] bg-border rounded-full overflow-hidden">
          <div
            className="h-full rounded-full animate-fill-bar"
            style={{
              width: `${feasibility * 100}%`,
              backgroundColor: getScoreColor(feasibility, 'feasibility'),
              boxShadow: `0 0 6px ${getScoreColor(feasibility, 'feasibility')}40`,
            }}
          />
        </div>
        <span className="text-[9px] font-mono text-text-secondary w-7 text-right tabular-nums">{feasibility.toFixed(2)}</span>
      </div>
    </div>
  )
}
