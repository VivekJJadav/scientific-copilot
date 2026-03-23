import { clsx } from 'clsx'

interface ScoreBadgeProps {
  score: number
  label?: string
}

export function ScoreBadge({ score, label }: ScoreBadgeProps) {
  const color =
    score >= 0.7
      ? 'bg-green-500/20 text-green-400'
      : score >= 0.5
      ? 'bg-amber-500/20 text-amber-400'
      : 'bg-red-500/20 text-red-400'

  return (
    <span className={clsx('inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium', color)}>
      {label && <span className="text-gray-500">{label}</span>}
      {score.toFixed(2)}
    </span>
  )
}
